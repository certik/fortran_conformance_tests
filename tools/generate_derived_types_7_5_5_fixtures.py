#!/usr/bin/env python3
"""Generate additional finite 7.5.5 type-bound procedure runtime fixtures."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SECTION = "7.5.5"
CATALOGUE = "doc/catalogues/derived_types_7_5_5.json"
PREFIX = "derived_types_755_"

SELECTED = {
    "S7.5.5-003": ["declared-versus-dynamic-source-use"],
    "S7.5.5-005": ["inherited-default-origin"],
    "S7.5.5-006": ["nameless-binding-access-source-use"],
}

RESTORED_PENDING = {
    "C780": {
        "operand-and-generic-effects-source-use": (
            "PENDING after DTFR-001 — Source-use at 15.4.3.4.2 p2-p3 and 15.5.6: "
            "unary operand maps to the sole dummy, binary left/right to first/second; extending "
            "one relational spelling extends its equivalent spelling. A later runtime must check "
            "separately assigned exact integer/logical results from fully defined operands, not "
            "just successful operator parsing. C780 only imports the interface requirement."
        ),
    },
    "C781": {
        "parenthesized-rhs-and-effect-source-use": (
            "PENDING after DTFR-001 — Source-use: later runtime may assign scalar integer 7 to "
            "a live t LHS through a subroutine that writes lhs%value=rhs. The public result query "
            "must yield 7 after return; use INOUT and no finalizable/pointer/allocatable components. "
            "Parenthesized RHS has no POINTER/ALLOCATABLE/TARGET attribute. Own the effect at "
            "10.2.1.4-.5 and 15.4.3.4.3 p2, not a duplicate C781 program."
        ),
    },
    "C785": {
        "nonfirst-dummy-name-source-use": (
            "PENDING after DTFR-002 — Source-use: canonical 7.5.4.5 p4 and 15.5.2.1-.2 runtime "
            "selects the second dummy self while reduced-list positional/keyword arguments fill "
            "the first. With defined receiver payload 7 and other integer 3, return 73 from "
            "10*self%value+other; C785 only requires the named dummy to exist."
        ),
    },
    "C789": {
        "concrete-implementation-source-use": (
            "PENDING after DTFR-003 — Source-use: preserve C738_valid__concrete_override and the "
            "canonical 7.5.7.3 interface/correspondence rules. Concrete implementation of every "
            "inherited deferred binding can permit a nonabstract child; C789 is reached only by a "
            "DEFERRED overriding binding and no duplicate positive-only link is created."
        ),
    },
    "C790": {
        "dispatch-source-use": (
            "PENDING after DTFR-003 — Source-use at 15.5.6/7.5.7.2: a live concrete child passed "
            "to CLASS(parent) has child dynamic type; an ordinary overridden specific may return "
            "22 rather than parent implementation 11, whereas an inherited NON_OVERRIDABLE "
            "implementation remains the parent's procedure. C790 is reached by an attempted "
            "override of a NON_OVERRIDABLE binding, not by an inheritance-only positive."
        ),
    },
}

ORACLE_PREFIX = "Batch177 derived-types 7.5.5 fixtures: "
LIMIT_PREFIX = "Batch177 derived-types 7.5.5 fixture boundaries: "

ORACLE_TEXT = {
    "S7.5.5-003": (
        "one runtime program separates declared generic selection from dynamic specific "
        "dispatch. Through a CLASS(parent) view, `choose(2)` selects the parent-declared "
        "integer generic member and then resolves the corresponding child override, "
        "returning 42. A child-only real branch remains callable only through a child "
        "declared type and returns 403."
    ),
    "S7.5.5-005": (
        "one runtime program inherits a public parent binding into a child whose own "
        "binding part contains PRIVATE. A client call through the public child object "
        "still reaches the inherited binding and returns 17, while the child's own "
        "explicitly public binding returns 18."
    ),
    "S7.5.5-006": (
        "one runtime program exposes a public nameless type-bound operator through an "
        "accessible object while keeping the specific binding and implementation private. "
        "The `.get.` expression returns 17; an alternate private specific target returns 18."
    ),
}

LIMIT_TEXT = {
    rule: (
        "Only the listed facet is represented by this companion packet. The fixture observes "
        "defined scalar integer results from live ordinary objects; it does not assert storage "
        "layout, vtable shape, finalization order, private representation access, diagnostic "
        "wording, or every canonical interface condition of the referenced dependency clauses. "
        "Compile-only wrapper/source-use facets and facets already bound by the type_bound_ "
        "packet remain outside this generator."
    )
    for rule in SELECTED
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source(text):
    text = text.strip("\n") + "\n"
    text.encode("ascii")
    if max(map(len, text.splitlines()), default=0) > 132:
        raise ValueError("unintended line-length boundary")
    return text


def case_id(rule, stem):
    return f"{rule.replace('.', '_').replace('-', '_')}_valid__{PREFIX}{stem}"


def manifest(spec):
    return {
        "schema_version": 1,
        "id": spec["id"],
        "rule": spec["rule"],
        "facets": spec["facets"],
        "evidence": "effect",
        "standard": "f2023",
        "files": ["source.f90"],
        "build": [
            {
                "id": "source",
                "source": "source.f90",
                "language": "fortran",
                "form": "free",
                "output": "source.o",
            }
        ],
        "link": {"driver": "fortran", "objects": ["source.o"], "output": "program"},
        "expect": {
            "phase": "run",
            "outcome": "success",
            "exit_code": 0,
            "stdout": spec["stdout"],
            "stderr": "",
        },
    }


def mutation(source_text, replacements, mutation_id, derivation):
    if isinstance(replacements, tuple):
        replacements = [replacements]
    spans = []
    for expected, replacement in replacements:
        if source_text.count(expected) != 1:
            raise ValueError(f"{mutation_id}: nonunique mutation span {expected!r}")
        if expected == replacement:
            raise ValueError(f"{mutation_id}: replacement is identical")
        start = source_text.index(expected)
        spans.append({
            "expected": expected,
            "replacement": replacement,
            "span": [start, start + len(expected)],
        })
    return {"id": mutation_id, "replacements": spans, "derivation": derivation}


def runtime_spec(rule, stem, source_text, stdout, derivation, mutations):
    text = source(source_text)
    spec = {
        "id": case_id(rule, stem),
        "stem": stem,
        "rule": rule,
        "facets": SELECTED[rule],
        "source": text,
        "stdout": stdout,
        "source_derivation": derivation,
        "source_sha256": sha(text.encode("ascii")),
        "mutations": mutations(text),
    }
    spec["manifest"] = manifest(spec)
    return spec


def specs():
    result = []

    result.append(runtime_spec(
        "S7.5.5-003",
        "declared_generic_dynamic_specific",
        """
module derived_types_755_dynamic_specific
implicit none
type :: parent
  integer :: payload
contains
  procedure :: value => parent_value
  generic :: choose => value
end type
type, extends(parent) :: child
contains
  procedure :: value => child_value
  procedure :: real_value => child_real_value
  generic :: choose => real_value
end type
contains
integer function parent_value(self, n) result(value)
  class(parent), intent(in) :: self
  integer, intent(in) :: n
  value = self%payload + n
end function
integer function child_value(self, n) result(value)
  class(child), intent(in) :: self
  integer, intent(in) :: n
  value = 10*self%payload + n
end function
integer function child_value_shifted(self, n) result(value)
  class(child), intent(in) :: self
  integer, intent(in) :: n
  value = 10*self%payload + n + 1
end function
integer function child_real_value(self, x) result(value)
  class(child), intent(in) :: self
  real, intent(in) :: x
  value = 100*self%payload + int(x)
end function
end module
program main
use derived_types_755_dynamic_specific
implicit none
type(child), target :: actual
class(parent), pointer :: view
integer :: observed
actual%payload = 4
view => actual
observed = view%choose(2)
if (observed /= 42) error stop 1
observed = actual%choose(3.0)
if (observed /= 403) error stop 2
print '(a)', 'derived_types_755 s003 dynamic specific ok'
end program
""",
        "derived_types_755 s003 dynamic specific ok\n",
        "7.5.5 p6 plus 15.5.6: the declared parent generic selects value, then dynamic type dispatches to child value.",
        lambda text: [
            mutation(
                text,
                ("procedure :: value => child_value", "procedure :: value => child_value_shifted"),
                "swap-child-corresponding-specific",
                "same declared generic member, child override returns 43"),
            mutation(
                text,
                ("procedure :: value => child_value", "procedure :: child_value_binding => child_value"),
                "remove-child-corresponding-override",
                "no corresponding child override, so parent value returns 6"),
        ]))




    result.append(runtime_spec(
        "S7.5.5-005",
        "inherited_public_default_origin",
        """
module derived_types_755_inherited_access
implicit none
type :: parent
  integer :: payload
contains
  procedure :: inherited => parent_value
end type
type, extends(parent) :: child
contains
  private
  procedure, public :: own => child_value
end type
type(child) :: object
contains
subroutine prepare()
  object%payload = 17
end subroutine
integer function parent_value(self) result(value)
  class(parent), intent(in) :: self
  value = self%payload
end function
integer function parent_value_shifted(self) result(value)
  class(parent), intent(in) :: self
  value = self%payload + 1
end function
integer function child_value(self) result(value)
  class(child), intent(in) :: self
  value = self%payload + 1
end function
end module
program main
use derived_types_755_inherited_access, only: object, prepare
implicit none
integer :: observed
call prepare()
observed = object%inherited()
if (observed /= 17) error stop 1
observed = object%own()
if (observed /= 18) error stop 2
print '(a)', 'derived_types_755 s005 inherited access ok'
end program
""",
        "derived_types_755 s005 inherited access ok\n",
        "7.5.5 p8 with 7.5.7.2: child's PRIVATE default does not reset inherited parent binding accessibility.",
        lambda text: [
            mutation(
                text,
                ("procedure :: inherited => parent_value", "procedure :: inherited => parent_value_shifted"),
                "swap-inherited-parent-target",
                "inherited public binding remains callable but returns 18"),
        ]))

    result.append(runtime_spec(
        "S7.5.5-006",
        "public_nameless_operator",
        """
module derived_types_755_public_operator
implicit none
private
type, public :: record
  private
  integer :: payload
contains
  procedure, private :: op_impl
  generic, public :: operator(.get.) => op_impl
end type
type(record), public :: object
public :: prepare
contains
subroutine prepare()
  object%payload = 17
end subroutine
integer function op_impl(self) result(value)
  class(record), intent(in) :: self
  value = self%payload
end function
integer function op_impl_shifted(self) result(value)
  class(record), intent(in) :: self
  value = self%payload + 1
end function
end module
program main
use derived_types_755_public_operator, only: object, prepare
implicit none
integer :: observed
call prepare()
observed = .get. object
if (observed /= 17) error stop 1
print '(a)', 'derived_types_755 s006 public nameless ok'
end program
""",
        "derived_types_755 s006 public nameless ok\n",
        "7.5.5 p9: a public nameless operator binding is accessible through the accessible public object.",
        lambda text: [
            mutation(
                text,
                ("procedure, private :: op_impl", "procedure, private :: op_impl => op_impl_shifted"),
                "swap-private-specific-target",
                "public operator still resolves but returns 18"),
        ]))


    return result


def build_corpus(root=ROOT):
    root = Path(root)
    files = {}
    built = {}
    for spec in specs():
        dirname = f"tests/fixtures/{PREFIX}{spec['stem']}"
        spec["path"] = dirname + "/fixture.json"
        built[spec["id"]] = spec
        files[root / dirname / "source.f90"] = spec["source"].encode("ascii")
        files[root / dirname / "fixture.json"] = (json.dumps(spec["manifest"], indent=2) + "\n").encode("ascii")
    return files, built


def owned_paragraph(text, prefix, replacement):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned 7.5.5 oracle paragraph")
    if matches:
        paragraphs[matches[0]] = replacement
    else:
        paragraphs.append(replacement)
    return "\n\n".join(paragraphs)


def remove_owned_paragraph(text, prefix):
    paragraphs = text.split("\n\n") if text else []
    matches = [index for index, paragraph in enumerate(paragraphs) if paragraph.startswith(prefix)]
    if len(matches) > 1:
        raise ValueError("duplicate owned 7.5.5 oracle paragraph")
    if matches:
        del paragraphs[matches[0]]
    return "\n\n".join(paragraphs)


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in result["requirements"]}
    for rule, facets in RESTORED_PENDING.items():
        if rule not in by_rule:
            raise ValueError(f"restored {rule} facet definitions changed")
        row = by_rule[rule]
        for facet, note in facets.items():
            if facet not in row["facets"]:
                raise ValueError(f"restored {rule} facet definitions changed")
            row.setdefault("pending", {})[facet] = note
        row["oracle"] = remove_owned_paragraph(row.get("oracle", ""), ORACLE_PREFIX + rule + ": ")
        row["oracle_limitation"] = remove_owned_paragraph(
            row.get("oracle_limitation", ""), LIMIT_PREFIX + rule + ": ")
    for rule, facets in SELECTED.items():
        if rule not in by_rule or not set(facets) <= set(by_rule[rule]["facets"]):
            raise ValueError(f"selected {rule} facet definitions changed")
        row = by_rule[rule]
        for facet in facets:
            row["pending"].pop(facet, None)
        row["oracle"] = owned_paragraph(
            row.get("oracle", ""), ORACLE_PREFIX + rule + ": ", ORACLE_PREFIX + rule + ": " + ORACLE_TEXT[rule])
        row["oracle_limitation"] = owned_paragraph(
            row.get("oracle_limitation", ""), LIMIT_PREFIX + rule + ": ",
            LIMIT_PREFIX + rule + ": " + LIMIT_TEXT[rule])
    return result


def composed_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tools"))
    import generate_type_bound_fixtures as type_bound
    _, type_bound_specs, _ = type_bound.build_corpus(Path(root))
    return type_bound.render_view(catalogue, type_bound_specs)


def generate(root=ROOT, check=False, sync_catalogue=False):
    root = Path(root)
    files, built = build_corpus(root)
    catalogue_path = root / CATALOGUE
    catalogue = json.loads(catalogue_path.read_text())
    updated = synced_catalogue(catalogue)
    view = composed_view(updated, root)
    if check:
        stale = [path.relative_to(root).as_posix() for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        actual = {p for p in (root / "tests/fixtures").glob(PREFIX + "*/*") if p.is_file()}
        stale += [p.relative_to(root).as_posix() for p in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        view_path = root / "doc/fortran_2023_7_5_5.md"
        if view_path.read_text() != view:
            stale.append("doc/fortran_2023_7_5_5.md")
        if stale:
            raise SystemExit("stale derived-types 7.5.5 packet: " + ", ".join(sorted(stale)))
    else:
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if sync_catalogue:
            catalogue_path.write_text(json.dumps(updated, indent=2) + "\n")
            (root / "doc/fortran_2023_7_5_5.md").write_text(view)
    return built


def apply_mutation(spec, mutation_spec, identical=False):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("mutation is not bound to the complete parent input")
    output = raw
    for replacement in sorted(mutation_spec["replacements"], key=lambda item: item["span"][0], reverse=True):
        start, end = replacement["span"]
        expected = replacement["expected"].encode("ascii")
        if raw[start:end] != expected:
            raise ValueError("mutation span does not match expected bytes")
        new = expected if identical else replacement["replacement"].encode("ascii")
        output = output[:start] + new + output[end:]
    return output.decode("ascii")


def compiler_family(compiler):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return "lfortran"
    if "gfortran" in name:
        return "gfortran"
    return name


def compiler_command(compiler, std, source_path, output_path):
    command = [str(compiler)]
    if std:
        if str(std).startswith("-"):
            command.append(str(std))
        elif compiler_family(compiler) == "lfortran":
            command.append("--std=" + str(std))
        else:
            command.append("-std=" + str(std))
    command += [str(source_path), "-o", str(output_path)]
    return command


def run_source(compiler, std, case_dir, source_text, stdout):
    source_path = case_dir / "source.f90"
    exe = case_dir / "program"
    source_path.write_text(source_text)
    compile_run = subprocess.run(
        compiler_command(compiler, std, source_path, exe), cwd=case_dir, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    if compile_run.returncode != 0 or not exe.is_file():
        return {
            "status": "compile-fail",
            "returncode": compile_run.returncode,
            "stdout": compile_run.stdout,
            "stderr": compile_run.stderr,
        }
    run = subprocess.run([str(exe)], cwd=case_dir, text=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, timeout=60)
    passed = run.returncode == 0 and run.stdout == stdout and run.stderr == ""
    return {
        "status": "pass" if passed else "run-fail",
        "returncode": run.returncode,
        "stdout": run.stdout,
        "stderr": run.stderr,
    }


def mutation_matrix(root=ROOT, compiler=None, std="", vacuity_probe=False):
    root = Path(root)
    _, built = build_corpus(root)
    items = [(spec, mutation_spec) for spec in built.values() for mutation_spec in spec["mutations"]]
    if not items:
        raise SystemExit("no derived-types 7.5.5 mutations defined")
    token = sha((str(compiler) + str(std) + str(vacuity_probe)).encode())[:12]
    workspace = root / ".derived_types_755_mutation_runs" / token
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    try:
        report = []
        parent_failures = []
        survivors = []
        compile_failures = []
        probe_done = False
        for spec in built.values():
            parent_dir = workspace / (spec["stem"] + "_parent")
            parent_dir.mkdir()
            parent = run_source(compiler, std, parent_dir, spec["source"], spec["stdout"])
            if parent["status"] != "pass":
                parent_failures.append({"id": spec["id"], **parent})
                continue
            for index, mutation_spec in enumerate(spec["mutations"]):
                case_dir = workspace / f"{spec['stem']}_mut_{index:03d}"
                case_dir.mkdir()
                identical = vacuity_probe and not probe_done
                probe_done = probe_done or identical
                observed = run_source(
                    compiler, std, case_dir, apply_mutation(spec, mutation_spec, identical), spec["stdout"])
                row = {
                    "id": spec["id"],
                    "mutation": mutation_spec["id"],
                    "identical_probe": identical,
                    "status": observed["status"],
                    "failed": observed["status"] != "pass",
                    "returncode": observed["returncode"],
                    "stdout": observed["stdout"],
                    "stderr": observed["stderr"],
                }
                report.append(row)
                if observed["status"] == "pass":
                    survivors.append(row)
                elif observed["status"] == "compile-fail":
                    compile_failures.append(row)
        if parent_failures or compile_failures or survivors:
            raise RuntimeError(json.dumps({
                "parent_failures": parent_failures,
                "compile_failures": compile_failures[:5],
                "survivors": survivors[:5],
            }, indent=2))
        return report
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def vacuity_probe(root=ROOT, compiler=None, std=""):
    try:
        mutation_matrix(root, compiler, std, vacuity_probe=True)
    except RuntimeError as error:
        detail = json.loads(str(error))
        survivors = detail.get("survivors", [])
        if survivors and survivors[0].get("identical_probe"):
            return survivors[0]
        raise
    raise RuntimeError("vacuity probe did not produce an identical-mutant survivor")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sync-catalogue", action="store_true")
    parser.add_argument("--check-mutations", action="store_true")
    parser.add_argument("--vacuity-probe", action="store_true")
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--std", default="")
    args = parser.parse_args()
    modes = [args.check, args.sync_catalogue, args.check_mutations, args.vacuity_probe]
    if sum(map(bool, modes)) > 1:
        parser.error("--check, --sync-catalogue, --check-mutations and --vacuity-probe are separate operations")
    if (args.check_mutations or args.vacuity_probe) and not args.compiler:
        parser.error("mutation modes require --compiler")
    if args.check_mutations:
        report = mutation_matrix(args.root, args.compiler, args.std)
        print(f"Mutation check: {len(report)}/{len(report)} derived_types_755 mutants failed "
              f"for {args.compiler} ({args.std}).")
        return
    if args.vacuity_probe:
        survivor = vacuity_probe(args.root, args.compiler, args.std)
        print("Vacuity probe: identical mutant was reported as survivor "
              f"({survivor['id']}:{survivor['mutation']}).")
        return
    built = generate(args.root, args.check, args.sync_catalogue)
    facets = sum(len(spec["facets"]) for spec in built.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(built)} derived-types 7.5.5 cases "
          f"covering {facets} facets.")


if __name__ == "__main__":
    main()
