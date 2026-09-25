#!/usr/bin/env python3
"""Generate selected 8.6 attribute statement fixtures with permanent mutations."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from suite_data import render_requirement

TOPIC = "attribute_statements_8_6_a"
CATALOGUES = {
    "8.6.1": "doc/catalogues/accessibility_statement_8_6_1.json",
    "8.6.10": "doc/catalogues/optional_statement_8_6_10.json",
    "8.6.11": "doc/catalogues/parameter_statement_8_6_11.json",
}
VIEWS = {
    "8.6.1": "doc/fortran_2023_8_6_1.md",
    "8.6.10": "doc/fortran_2023_8_6_10.md",
    "8.6.11": "doc/fortran_2023_8_6_11.md",
}
MARKER = "Attribute statements 8.6.a fixture implementation:"

CHECKS = r'''
module attribute_8_6_a_checks
implicit none
integer :: checked = 0
contains
subroutine check_int(label, actual, expected)
character(*), intent(in) :: label
integer, intent(in) :: actual, expected
if (actual /= expected) then
  print *, 'CHECK_INT', trim(label), actual, expected
  error stop 1
end if
checked = checked + 1
end subroutine
subroutine check_true(label, actual)
character(*), intent(in) :: label
logical, intent(in) :: actual
if (.not. actual) then
  print *, 'CHECK_TRUE', trim(label)
  error stop 2
end if
checked = checked + 1
end subroutine
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
  print *, 'CHECK_COUNT', checked, expected
  error stop 3
end if
print '(a)', 'ATTRIBUTE STATEMENTS 8.6.A OK'
end subroutine
end module attribute_8_6_a_checks
'''.lstrip()


def body(text):
    return textwrap.dedent(text).strip() + "\n"


def manifest(spec):
    data = dict(
        schema_version=1,
        id=spec["id"],
        rule=spec["rule"],
        facets=spec["facets"],
        standard="f2023",
        evidence=spec.get("evidence", "effect"),
        files=["source.f90"],
        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
    )
    if spec.get("phase") == "compile":
        data["expect"] = dict(phase="compile", step="source", outcome=spec["outcome"])
        if "diagnostic" in spec:
            data["expect"]["diagnostic"] = spec["diagnostic"]
    else:
        data["link"] = dict(objects=["source.o"], output="program")
        data["expect"] = dict(
            phase="run",
            outcome="success",
            exit_code=0,
            stdout="ATTRIBUTE STATEMENTS 8.6.A OK\n",
            stderr="",
        )
    return json.dumps(data, indent=2) + "\n"


def m(mid, facet, assertion, old, new):
    return dict(id=mid, facet=facet, assertion=assertion, changes=[dict(old=old, new=new)])


def mg(mid, facet, assertion, changes):
    return dict(id=mid, facet=facet, assertion=assertion, changes=[dict(old=o, new=n) for o, n in changes])


def build_specs():
    specs = []

    access_source = CHECKS + body(r'''
        module a861_provider
        implicit none
        private
        integer, parameter :: pconst = 17
        integer :: var_public = 23
        type :: t_public
          integer :: n = 37
        end type t_public
        interface gen
          module procedure gen_i
        end interface
        interface operator(+)
          module procedure add_t
        end interface
        interface assignment(=)
          module procedure assign_t
        end interface
        public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)
        contains
        integer function proc_public()
        proc_public = 41
        end function proc_public
        integer function gen_i(x)
integer, intent(in) :: x
        gen_i = x + 5
        end function gen_i
        function add_t(a, b) result(r)
type(t_public), intent(in) :: a, b
type(t_public) :: r
        r%n = a%n + b%n + 1
        end function add_t
        subroutine assign_t(lhs, rhs)
type(t_public), intent(out) :: lhs
integer, intent(in) :: rhs
        lhs%n = rhs + 2
        end subroutine assign_t
        end module a861_provider
        module a861_receiver
        use a861_provider
        implicit none
        private
        integer, parameter :: local_public = 43
        integer :: local_private = 47
        public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)
        public :: local_public
        private :: local_private
        contains
        integer function receiver_private_value()
        receiver_private_value = local_private
        end function receiver_private_value
        end module a861_receiver
        module a861_fallbacks
        use a861_provider, only: t_public
        implicit none
        private
        interface gen
          module procedure fallback_gen
        end interface
        interface operator(+)
          module procedure fallback_add_t
        end interface
        interface assignment(=)
          module procedure fallback_assign_t
        end interface
        public :: gen, operator(+), assignment(=)
        contains
        integer function fallback_gen(x)
        integer, intent(in) :: x
        fallback_gen = x + 105
        end function fallback_gen
        function fallback_add_t(a, b) result(r)
        type(t_public), intent(in) :: a, b
        type(t_public) :: r
        r%n = a%n + b%n + 101
        end function fallback_add_t
        subroutine fallback_assign_t(lhs, rhs)
        type(t_public), intent(out) :: lhs
        integer, intent(in) :: rhs
        lhs%n = rhs + 102
        end subroutine fallback_assign_t
        end module a861_fallbacks
        program p
        use attribute_8_6_a_checks
        use a861_receiver
        implicit none
        type(t_public) :: assigned, left, right, summed, default_obj
        left%n = 2
        right%n = 3
        assigned = 5
        summed = left + right
        call check_int('access-named-constant', pconst, 17)
        call check_int('access-variable-name', var_public, 23)
        call check_int('access-procedure-name', proc_public(), 41)
        call check_int('access-generic-name', gen(3), 8)
        call check_int('access-assignment-generic', assigned%n, 7)
        call check_int('access-operator-generic', summed%n, 6)
        call check_int('access-nonintrinsic-type', default_obj%n, 37)
        call check_int('access-local-public', local_public, 43)
        call finish_checks(8)
end program p
    ''')
    specs.append(dict(
        id=f"{TOPIC}_accessibility_resolution",
        rule="R831",
        sections={"8.6.1": {"R831": ["generic-name-branch", "operator-generic-branch", "assignment-generic-branch"]}},
        facets=["generic-name-branch", "operator-generic-branch", "assignment-generic-branch"],
        source=access_source,
        checks=8,
        derivation="8.6.1 R830/R831 and p1 permit listed PUBLIC/PRIVATE statements, no-list defaults and generic-spec access IDs; direct USE resolution and defined generic calls observe the exported constant, variable, procedure, type, generic, operator and assignment identifiers.",
        mutants=[
            mg("access-private-constant-fallback", "named-constant-name", "access-named-constant", [
                ("public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)", "private :: pconst\n        public :: var_public, proc_public, t_public, gen, operator(+), assignment(=)"),
                ("        implicit none\n        type(t_public) :: assigned", "implicit none\n        integer, parameter :: pconst = 117\n        type(t_public) :: assigned"),
            ]),
            mg("access-private-variable-fallback", "variable-name", "access-variable-name", [
                ("public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)", "public :: pconst, proc_public, t_public, gen, operator(+), assignment(=)\n        private :: var_public"),
                ("        implicit none\n        type(t_public) :: assigned", "implicit none\n        integer :: var_public = 123\n        type(t_public) :: assigned"),
            ]),
            mg("access-private-procedure-fallback", "procedure-name", "access-procedure-name", [
                ("public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)", "public :: pconst, var_public, t_public, gen, operator(+), assignment(=)\n        private :: proc_public"),
                ("        call finish_checks(8)\nend program p", "        call finish_checks(8)\n        contains\n        integer function proc_public()\n        proc_public = 141\n        end function proc_public\nend program p"),
            ]),
            mg("access-private-generic-fallback", "generic-name-branch", "access-generic-name", [
                ("        integer :: local_private = 47\n        public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)", "        integer :: local_private = 47\n        public :: pconst, var_public, proc_public, t_public, operator(+), assignment(=)\n        private :: gen"),
                ("        use a861_receiver\n        implicit none", "        use a861_receiver\n        use a861_fallbacks, only: gen\n        implicit none"),
            ]),
            mg("access-private-operator-fallback", "operator-generic-branch", "access-operator-generic", [
                ("        integer :: local_private = 47\n        public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)", "        integer :: local_private = 47\n        public :: pconst, var_public, proc_public, t_public, gen, assignment(=)\n        private :: operator(+)"),
                ("        use a861_receiver\n        implicit none", "        use a861_receiver\n        use a861_fallbacks, only: operator(+)\n        implicit none"),
            ]),
            mg("access-private-assignment-fallback", "assignment-generic-branch", "access-assignment-generic", [
                ("        integer :: local_private = 47\n        public :: pconst, var_public, proc_public, t_public, gen, operator(+), assignment(=)", "        integer :: local_private = 47\n        public :: pconst, var_public, proc_public, t_public, gen, operator(+)\n        private :: assignment(=)"),
                ("        use a861_receiver\n        implicit none", "        use a861_receiver\n        use a861_fallbacks, only: assignment(=)\n        implicit none"),
            ]),
            m("access-type-default", "nonintrinsic-type-name", "access-nonintrinsic-type", "integer :: n = 37", "integer :: n = 38"),
            m("access-local-public-value", "local-default-forms", "access-local-public", "integer, parameter :: local_public = 43", "integer, parameter :: local_public = 44"),
            m("access-listed-identifier-value", "listed-individual-identifiers", "access-variable-name", "integer :: var_public = 23", "integer :: var_public = 24"),
            m("access-specific-generic-value", "generic-versus-specific-access", "access-generic-name", "gen_i = x + 5", "gen_i = x + 6"),
            m("access-omitted-private-default", "omitted-list-forms", "access-local-public", "private\n        integer, parameter :: local_public", "public\n        integer, parameter :: local_public"),
            m("access-listed-public-form", "listed-public-private-forms", "access-named-constant", "integer, parameter :: pconst = 17", "integer, parameter :: pconst = 18"),
            m("access-explicit-origin", "explicit-access-and-origin-boundaries", "access-local-public", "integer :: local_private = 47", "integer :: local_private = 48"),
        ],
    ))

    optional_source = CHECKS + body(r'''
        program p
        use attribute_8_6_a_checks
        implicit none
        integer :: total
        total = 0
        call observe(10)
        call observe(10, 20, 30)
        call check_int('optional-present-total', total, 60)
        call finish_checks(1)
        contains
        subroutine observe(required, with_colon, plain)
        integer, intent(in) :: required
        integer, intent(in) :: with_colon, plain
        optional :: with_colon
        optional plain
        if (present(with_colon)) then
          total = total + with_colon
        else
          total = total + required
        end if
        if (present(plain)) total = total + plain
        end subroutine observe
end program p
    ''')
    specs.append(dict(
        id=f"{TOPIC}_optional_presence",
        rule="R853",
        sections={"8.6.10": {"R853": ["presence-and-interface-source"]}},
        facets=["presence-and-interface-source"],
        source=optional_source,
        checks=1,
        derivation="8.6.10 R853 and p1 specify OPTIONAL statements for listed dummy arguments; PRESENT distinguishes omitted from supplied data dummies through an explicit internal interface.",
        mutants=[
            m("optional-presence-branch", "presence-and-interface-source", "optional-present-total", "if (present(with_colon)) then", "if (.not. present(with_colon)) then"),
        ],
    ))

    parameter_source = CHECKS + body(r'''
        program p
        use attribute_8_6_a_checks
        implicit none
        type :: pair_t
          integer :: left
          integer :: right
        end type pair_t
        integer :: basis, literal, named, vector(2)
        type(pair_t) :: pair
        logical explicit_logical
        parameter (basis=3)
        parameter (literal=7, named=basis+4)
        parameter (vector=[3,7])
        parameter (pair=pair_t(11,13))
        parameter (explicit_logical=.true.)
        call late_implicit
        call check_int('parameter-literal', literal, 7)
        call check_int('parameter-named-expression', named, 7)
        call check_true('parameter-prior-explicit-logical', explicit_logical)
        call check_true('parameter-vector-shape', all(shape(vector) == [2]))
        call check_int('parameter-vector-element', vector(2), 7)
        call check_int('parameter-derived-left', pair%left, 11)
        call check_int('parameter-derived-right', pair%right, 13)
        call finish_checks(8)
        contains
        subroutine late_implicit
        implicit integer(n)
        parameter (n=2)
        integer n
        call check_int('parameter-late-matching-integer', n, 2)
        end subroutine late_implicit
end program p
    ''')
    specs.append(dict(
        id=f"{TOPIC}_parameter_definitions",
        rule="S8.6.11-004",
        sections={"8.6.11": {"S8.6.11-004": ["simple-derived-values"]}},
        facets=["simple-derived-values"],
        source=parameter_source,
        checks=8,
        derivation="8.6.11 R854/R855 and p2-p4 define named constants by PARAMETER; direct checks of actual constants observe literal, named-expression, late implicit matching, prior explicit type, prior rank, array conformance and derived constructor values.",
        mutants=[
            m("parameter-single-basis", "single-definition-form", "parameter-named-expression", "parameter (basis=3)", "parameter (basis=4)"),
            m("parameter-multiple-literal", "multiple-definition-form", "parameter-literal", "parameter (literal=7, named=basis+4)", "parameter (literal=8, named=basis+4)"),
            m("parameter-literal-value", "literal-definition", "parameter-literal", "literal=7", "literal=8"),
            m("parameter-named-expression", "named-expression-definition", "parameter-named-expression", "named=basis+4", "named=basis+5"),
            m("parameter-late-implicit", "late-matching-integer-control", "parameter-late-matching-integer", "parameter (n=2)", "parameter (n=3)"),
            m("parameter-prior-logical", "prior-explicit-type-boundary", "parameter-prior-explicit-logical", "parameter (explicit_logical=.true.)", "parameter (explicit_logical=.false.)"),
            m("parameter-prior-array", "prior-type-array-spec", "parameter-vector-shape", "integer :: basis, literal, named, vector(2)", "integer :: basis, literal, named, vector(3)"),
            m("parameter-array-conformance", "explicit-shape-array-conformance", "parameter-vector-element", "parameter (vector=[3,7])", "parameter (vector=[3,8])"),
            m("parameter-derived-left", "simple-derived-values", "parameter-derived-left", "parameter (pair=pair_t(11,13))", "parameter (pair=pair_t(12,13))"),
        ],
    ))

    c873_invalid_source = body(r'''
        module a861_c873_invalid
        implicit none
        private
        private
        integer :: token
        end module a861_c873_invalid
    ''')
    specs.append(dict(
        id=f"{TOPIC}_c873_duplicate_omitted_private",
        rule="C873",
        sections={"8.6.1": {"C873": ["one-no-list-default"]}},
        facets=["one-no-list-default"],
        source=c873_invalid_source,
        phase="compile",
        outcome="diagnose",
        checks=0,
        diagnostic=dict(file="source.f90", line=4, end_line=4, excludes_any=[
            "not implemented", "unimplemented", "unsupported", "internal error", "asr",
            "verifier", "out of memory", "cannot read module", "missing module"]),
        derivation="8.6.1 C873 permits only one accessibility statement with an omitted access-id-list in a module specification part; the second bare PRIVATE is the single offending property.",
        mutants=[],
    ))

    c873_control_source = body(r'''
        module a861_c873_control
        implicit none
        private
        integer :: token
        end module a861_c873_control
    ''')
    specs.append(dict(
        id=f"{TOPIC}_c873_single_omitted_private_control",
        rule="C873",
        sections={},
        facets=["one-no-list-default"],
        source=c873_control_source,
        phase="compile",
        outcome="success",
        evidence="positive-control",
        checks=0,
        derivation="One-property control for C873 duplicate omitted-list PRIVATE: deleting the second bare PRIVATE leaves exactly one omitted-list access statement.",
        mutants=[],
    ))
    return {spec["id"]: spec for spec in specs}


def all_bindings(specs):
    result = {}
    for spec in specs.values():
        for section, rules in spec["sections"].items():
            for rule, facets in rules.items():
                result.setdefault(section, {}).setdefault(rule, []).append((spec, facets))
    return result


def build_corpus(root=ROOT):
    specs = build_specs()
    files = {}
    for spec in specs.values():
        directory = Path(root) / "tests" / "fixtures" / spec["id"]
        spec["source_path"] = (directory / "source.f90").relative_to(root).as_posix()
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = manifest(spec).encode("ascii")
    return files, specs


def strip_owned(text):
    parts = text.split("\n\n" + MARKER)
    if len(parts) == 1:
        return text.rstrip()
    return parts[0].rstrip()


def synced_catalogue(section, catalogue, specs):
    result = json.loads(json.dumps(catalogue))
    bindings = all_bindings(specs).get(section, {})
    for req in result["requirements"]:
        selected = bindings.get(req["id"], [])
        if not selected:
            continue
        covered = []
        details = []
        for spec, facets in selected:
            covered.extend(facets)
            kind = "compile diagnostic/control" if spec.get("phase") == "compile" else f"{spec['checks']} run-time assertion(s)"
            details.append(f"`{spec['id']}` covers " + ", ".join(f"`{f}`" for f in facets) + f" with {kind}")
        for facet in covered:
            if facet not in req["facets"]:
                raise ValueError(f"{section} {req['id']}: unknown facet {facet}")
            req["pending"].pop(facet, None)
        paragraph = (MARKER + " " + "; ".join(details) + ". Runtime covered facets have named assertions and conforming feature mutations that compile and fail at run time on both checked toolchains; diagnostic facets have a one-property conforming control and a line-anchored excludes-only diagnostic oracle. Oracles use exact INTEGER values, LOGICAL inquiry/PRESENT results, direct inquiries, and same-source constant values only.")
        req["oracle"] = strip_owned(req.get("oracle", "")) + "\n\n" + paragraph
        remain = len(req.get("pending", {}))
        req["oracle_limitation"] = strip_owned(req.get("oracle_limitation", "")) + (f"\n\n{MARKER} {len(covered)} facet(s) are fixture-backed here and {remain} remain pending. The fixtures do not claim coarray behavior, module-name access policies rejected by the reference compiler, defined-I/O generics, diagnostic wording, source-use inventory credit, or unselected grammar/source-gate facets.")
    return result


def render_view(section, catalogue, root=ROOT):
    path = Path(root) / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if begin not in text or end not in text:
        raise ValueError(f"{VIEWS[section]} lacks generated boundaries")
    prefix = text.split(begin, 1)[0]
    suffix = text.split(end, 1)[1]
    if section == "8.6.10":
        prefix = prefix.replace(
            "This source-only packet introduces pending plans, not execution.",
            "The original source-only packet introduced pending plans; the bounded fixtures below add selected execution without granting approval.")
        prefix = prefix.replace(
            "No fixtures, compiler runs, profiles, links, SourceUses or approvals are\ncreated by this author packet. Current facet states remain in the catalogue.",
            "The original source registration supplied no fixtures, compiler runs, profiles, links, SourceUses or approvals. The attribute-statement generator supplies bounded fixtures for selected facets; current facet states remain in the catalogue.")
    if section == "8.6.2":
        prefix = prefix.replace(
            "the catalogue. This registration supplies no program, compiler observation,\ncanonical connection, source-use instance, fixture approval or baseline change.",
            "the catalogue. The original registration supplied no program, compiler observation, canonical connection, source-use instance, fixture approval or baseline change; the bounded fixtures below add selected execution without review approval.")
    content = "\n".join(render_requirement(req) for req in catalogue["requirements"])
    return prefix + begin + "\n\n" + content + "\n" + end + suffix.rstrip() + "\n"


def sync_files(root=ROOT):
    root = Path(root)
    files, specs = build_corpus(root)
    for path, raw in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    for section, rel in CATALOGUES.items():
        path = root / rel
        updated = synced_catalogue(section, json.loads(path.read_text()), specs)
        path.write_text(json.dumps(updated, indent=2) + "\n")
        (root / VIEWS[section]).write_text(render_view(section, updated, root))
    return files, specs


def check_files(root=ROOT):
    root = Path(root)
    files, specs = build_corpus(root)
    stale = [p.relative_to(root).as_posix() for p, raw in files.items() if not p.is_file() or p.read_bytes() != raw]
    actual = {p for p in (root / "tests" / "fixtures").glob(TOPIC + "_*/*") if p.is_file()}
    stale += [p.relative_to(root).as_posix() for p in sorted(actual - set(files))]
    for section, rel in CATALOGUES.items():
        path = root / rel
        current = json.loads(path.read_text())
        expected = synced_catalogue(section, current, specs)
        if current != expected:
            stale.append(rel)
        view = render_view(section, expected, root)
        if (root / VIEWS[section]).read_text() != view:
            stale.append(VIEWS[section])
    if stale:
        raise SystemExit("stale attribute_statements_8_6_a packet: " + ", ".join(sorted(stale)))
    return files, specs


def compiler_command(compiler, std):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def run_mutations(compiler, std):
    _, specs = build_corpus(ROOT)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / f".mutation_{TOPIC}" / digest
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    total = 0
    try:
        for name, spec in specs.items():
            if spec.get("phase") == "compile":
                continue
            parent = spec["source"]
            facets = set()
            claimed = {facet for rules in spec["sections"].values() for fs in rules.values() for facet in fs}
            if not claimed:
                continue
            for mutant in spec["mutants"]:
                if mutant["facet"] not in claimed:
                    continue
                total += 1
                facets.add(mutant["facet"])
                mutated = parent
                for change in mutant["changes"]:
                    if mutated.count(change["old"]) != 1:
                        raise SystemExit(f"{name}/{mutant['id']}: mutation target count is not one")
                    mutated = mutated.replace(change["old"], change["new"], 1)
                if mutated == parent:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant did not change source")
                work = base / name / mutant["id"]
                work.mkdir(parents=True)
                src = work / "source.f90"
                exe = work / "program"
                src.write_text(mutated)
                built = subprocess.run(compiler_command(compiler, std) + [str(src), "-o", str(exe)], cwd=work,
                                       text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
                if built.returncode != 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant failed to compile\n{built.stdout}")
                ran = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, timeout=60)
                if ran.returncode == 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant survived")
            if not claimed <= facets:
                raise SystemExit(f"{name}: facets without mutants {sorted(claimed - facets)}")
        print(f"Mutation check failed all {total} mutants with {compiler} ({std}).")
    finally:
        shutil.rmtree(base, ignore_errors=True)
        if base.parent.exists() and not any(base.parent.iterdir()):
            base.parent.rmdir()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        run_mutations(args.compiler, args.std)
        return
    if args.check:
        files, specs = check_files(ROOT)
        action = "Checked"
    else:
        files, specs = sync_files(ROOT)
        action = "Generated"
    facets = sum(len(fs) for spec in specs.values() for rules in spec["sections"].values() for fs in rules.values())
    print(f"{action} {len(files)} files for {len(specs)} fixtures and {facets} facets.")


if __name__ == "__main__":
    main()
