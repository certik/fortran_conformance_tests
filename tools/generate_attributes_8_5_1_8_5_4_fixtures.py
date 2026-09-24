#!/usr/bin/env python3
"""Generate selected 8.5.1/8.5.2 attribute fixtures with permanent mutations."""
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

TOPIC = "attributes_8_5_1_8_5_4"
CATALOGUES = {
    "8.5.1": "doc/catalogues/attribute_specification_8_5_1.json",
    "8.5.2": "doc/catalogues/accessibility_attribute_8_5_2.json",
}
VIEWS = {
    "8.5.1": "doc/fortran_2023_8_5_1.md",
    "8.5.2": "doc/fortran_2023_8_5_2.md",
}
MARKER = "Attributes 8.5.1/8.5.2 fixture implementation:"

CHECKS = """
module attribute_8_5_checks
implicit none
private
integer, save :: checked = 0
public :: check_int, check_true, finish_checks
contains
subroutine fail(label)
character(*), intent(in) :: label
print *, 'CHECK_FAILED', label
error stop 99
end subroutine fail
subroutine check_int(label, actual, expected)
character(*), intent(in) :: label
integer, intent(in) :: actual, expected
if (actual /= expected) then
print *, 'CHECK_INT', label, actual, expected
error stop 1
end if
checked = checked + 1
end subroutine check_int
subroutine check_true(label, actual)
character(*), intent(in) :: label
logical, intent(in) :: actual
if (.not. actual) call fail(label)
checked = checked + 1
end subroutine check_true
subroutine finish_checks(expected)
integer, intent(in) :: expected
if (checked /= expected) then
print *, 'CHECK_COUNT', checked, expected
error stop 2
end if
end subroutine finish_checks
end module attribute_8_5_checks
""".lstrip()


def body(text):
    return textwrap.dedent(text).strip() + "\n"


def manifest(spec):
    data = dict(
        schema_version=1,
        id=spec["id"],
        rule=spec["rule"],
        facets=spec["facets"],
        standard="f2023",
        evidence=spec["evidence"],
        files=["source.f90"],
        build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
        link=dict(objects=["source.o"], output="program"),
        expect=dict(phase="run", outcome="success", exit_code=0),
    )
    return json.dumps(data, indent=2) + "\n"


def case_dir(case_id):
    return f"tests/fixtures/{case_id}"


def m(mid, facet, assertion, old, new):
    return dict(id=mid, facet=facet, assertion=assertion, old=old, new=new)


def mg(mid, facet, assertion, changes):
    return dict(id=mid, facet=facet, assertion=assertion,
                changes=[dict(old=old, new=new) for old, new in changes])


def build_specs():
    specs = []

    c816_source = CHECKS + body(r"""
        module c816_result_shapes
        implicit none
        contains
        function fixed_result() result(r)
        integer :: r(2,3)
        integer :: i, j
        do j = 1, 3
          do i = 1, 2
            r(i,j) = 10*i + j
          end do
        end do
        end function fixed_result
        function sized_result(n) result(r)
        integer, intent(in) :: n
        integer :: r(n)
        integer :: i
        do i = 1, n
          r(i) = 100 + i
        end do
        end function sized_result
        end module c816_result_shapes
        program p
        use attribute_8_5_checks
        use c816_result_shapes
        implicit none
        call check_true('c816-explicit-list-shape', all(shape(fixed_result()) == [2,3]))
        call check_true('c816-specification-bound-shape', all(shape(sized_result(4)) == [4]))
        call finish_checks(2)
        end program p
    """)
    specs.append(dict(
        id=f"{TOPIC}_c816_function_results",
        rule="C816",
        facets=["explicit-list-admission", "specification-bound-list"],
        evidence="effect",
        source=c816_source,
        checks=2,
        derivation="8.5.1 C816 requires a nonallocatable nonpointer function result array-spec to be an explicit-shape-spec-list; direct SHAPE inquiries on the function expressions require [2,3] and [4].",
        mutants=[
            m("c816-fixed-result-second-bound", "explicit-list-admission", "c816-explicit-list-shape", "integer :: r(2,3)", "integer :: r(2,2)"),
            m("c816-specification-bound-expression", "specification-bound-list", "c816-specification-bound-shape", "integer :: r(n)", "integer :: r(n+1)"),
        ],
    ))

    r807_source = CHECKS + body(r"""
        module r807_forms
        implicit none
        integer, public :: r807_public_value = 17
        integer, private :: r807_private_value = 23
        type, public :: r807_public_type
          integer :: n = 31
        end type r807_public_type
        type, private :: r807_private_type
          integer :: n = 37
        end type r807_private_type
        end module r807_forms
        program p
        use attribute_8_5_checks
        use r807_forms
        implicit none
        integer :: r807_private_value = 61
        type :: r807_private_type
          integer :: n = 67
        end type r807_private_type
        type(r807_public_type) :: public_object
        type(r807_private_type) :: private_object
        call check_int('r807-public-form-value', r807_public_value, 17)
        call check_int('r807-private-form-fallback-value', r807_private_value, 61)
        call check_int('r807-public-form-type', public_object%n, 31)
        call check_int('r807-private-form-type-fallback', private_object%n, 67)
        call finish_checks(4)
        end program p
    """)
    specs.append(dict(
        id=f"{TOPIC}_r807_access_spec_forms",
        rule="R807",
        facets=["public-form", "private-form"],
        evidence="positive-control",
        source=r807_source,
        checks=4,
        derivation="8.5.2 R807 has PUBLIC and PRIVATE alternatives; module declarations using each form compile and the use scope resolves public identifiers to provider values while private identifiers resolve to local sentinels.",
        mutants=[
            mg("r807-public-keyword-private-provider", "public-form", "r807-public-form-value", [
                ("integer, public :: r807_public_value = 17", "integer, private :: r807_public_value = 17"),
                ("integer :: r807_private_value = 61", "integer :: r807_public_value = 117, r807_private_value = 61"),
            ]),
            mg("r807-private-keyword-public-provider", "private-form", "r807-private-form-fallback-value", [
                ("integer, private :: r807_private_value = 23", "integer, public :: r807_private_value = 23"),
                ("integer :: r807_private_value = 61", "! r807_private_value local sentinel removed"),
            ]),
        ],
    ))

    c817_source = CHECKS + body(r"""
        module c817_module_specification_part
        implicit none
        integer, public :: c817_admitted_public = 41
        integer, private :: c817_admitted_private = 43
        end module c817_module_specification_part
        program p
        use attribute_8_5_checks
        use c817_module_specification_part
        implicit none
        integer :: c817_admitted_private = 143
        call check_int('c817-module-public-access-spec', c817_admitted_public, 41)
        call check_int('c817-module-private-access-spec', c817_admitted_private, 143)
        call finish_checks(2)
        end program p
    """)
    specs.append(dict(
        id=f"{TOPIC}_c817_module_admission",
        rule="C817",
        facets=["module-admission"],
        evidence="positive-control",
        source=c817_source,
        checks=2,
        derivation="8.5.2 C817 permits access-specs in a module specification-part; the public declaration is use-associated and the private declaration is not, so the local sentinel is selected.",
        mutants=[
            mg("c817-module-admission-public-to-private", "module-admission", "c817-module-public-access-spec", [
                ("integer, public :: c817_admitted_public = 41", "integer, private :: c817_admitted_public = 41"),
                ("integer :: c817_admitted_private = 143", "integer :: c817_admitted_public = 141, c817_admitted_private = 143"),
            ]),
        ],
    ))

    s001_source = CHECKS + body(r"""
        module s852_declaration_subjects
        implicit none
        integer, public :: list_public_a = 11, list_public_b = 13
        integer, private :: list_private_a = 17, list_private_b = 19
        type, public :: exported_t
          integer :: n = 23
        end type exported_t
        type, private :: hidden_t
          integer :: n = 29
        end type hidden_t
        end module s852_declaration_subjects
        program p
        use attribute_8_5_checks
        use s852_declaration_subjects
        implicit none
        integer :: list_private_a = 117, list_private_b = 119
        type :: hidden_t
          integer :: n = 129
        end type hidden_t
        type(exported_t) :: exported_object
        type(hidden_t) :: hidden_object
        call check_true('s852-declaration-list-public-names', all([list_public_a, list_public_b] == [11,13]))
        call check_true('s852-declaration-list-private-fallbacks', all([list_private_a, list_private_b] == [117,119]))
        call check_int('s852-derived-type-public-name', exported_object%n, 23)
        call check_int('s852-derived-type-private-fallback', hidden_object%n, 129)
        call finish_checks(4)
        end program p
    """)
    specs.append(dict(
        id=f"{TOPIC}_s852_declaration_subjects",
        rule="S8.5.2-001",
        facets=["declaration-list-names", "derived-type-name"],
        evidence="effect",
        source=s001_source,
        checks=4,
        derivation="8.5.2 p2 says a type-declaration access-spec applies to all entity names in that statement and a derived-type-stmt access-spec applies to the type name; public subjects are use-associated and private subjects select same-named local sentinels.",
        mutants=[
            mg("s852-list-private-provider-public", "declaration-list-names", "s852-declaration-list-private-fallbacks", [
                ("integer, private :: list_private_a = 17, list_private_b = 19", "integer, public :: list_private_a = 17, list_private_b = 19"),
                ("integer :: list_private_a = 117, list_private_b = 119", "! list_private_a/list_private_b local sentinels removed"),
            ]),
            mg("s852-hidden-type-public", "derived-type-name", "s852-derived-type-private-fallback", [
                ("type, private :: hidden_t\n  integer :: n = 29\nend type hidden_t", "type, public :: hidden_t\n  integer :: n = 29\nend type hidden_t"),
                ("type :: hidden_t\n  integer :: n = 129\nend type hidden_t", "! hidden_t local type sentinel removed"),
            ]),
        ],
    ))

    s002_source = CHECKS + body(r"""
        module s852_implicit_default
        implicit none
        integer :: implicit_public = 31
        end module s852_implicit_default
        module s852_nolist_public
        implicit none
        public
        integer :: no_list_public = 37
        end module s852_nolist_public
        module s852_nolist_private
        implicit none
        private
        integer :: no_list_private = 41
        end module s852_nolist_private
        module s852_explicit_public_module
        implicit none
        private
        public :: explicit_public
        integer :: explicit_public = 43
        end module s852_explicit_public_module
        module s852_explicit_private_module
        implicit none
        public
        private :: explicit_private
        integer :: explicit_private = 47
        end module s852_explicit_private_module
        module s852_origin_default
        implicit none
        integer, public :: origin_default = 53
        end module s852_origin_default
        module s852_middle_default
        use s852_origin_default, only: imported_default => origin_default
        implicit none
        private
        end module s852_middle_default
        program p
        use attribute_8_5_checks
        use s852_implicit_default
        use s852_nolist_public
        use s852_nolist_private
        use s852_explicit_public_module
        use s852_explicit_private_module
        use s852_middle_default
        implicit none
        integer :: no_list_private = 141, explicit_private = 147, imported_default = 153
        call check_int('s852-implicit-public-local', implicit_public, 31)
        call check_int('s852-no-list-public', no_list_public, 37)
        call check_int('s852-no-list-private-local', no_list_private, 141)
        call check_int('s852-explicit-public-in-private-default', explicit_public, 43)
        call check_int('s852-explicit-private-in-public-default', explicit_private, 147)
        call check_int('s852-use-associated-local-default', imported_default, 153)
        call finish_checks(6)
        end program p
    """)
    specs.append(dict(
        id=f"{TOPIC}_s852_defaults_and_imports",
        rule="S8.5.2-002",
        facets=["implicit-public-local", "no-list-public", "no-list-private-local", "explicit-identifier-access", "use-associated-local-default"],
        evidence="effect",
        source=s002_source,
        checks=6,
        derivation="8.5.2 p3-p4 and 8.6.1 defaults are observed by resolving module identifiers through USE: ordinary/public defaults import provider values, while private defaults or explicit PRIVATE select local sentinels.",
        mutants=[
            mg("s852-implicit-default-to-private", "implicit-public-local", "s852-implicit-public-local", [
                ("module s852_implicit_default\nimplicit none\ninteger :: implicit_public = 31", "module s852_implicit_default\nimplicit none\nprivate\ninteger :: implicit_public = 31"),
                ("integer :: no_list_private = 141, explicit_private = 147, imported_default = 153", "integer :: implicit_public = 131, no_list_private = 141, explicit_private = 147, imported_default = 153"),
            ]),
            mg("s852-no-list-public-to-private", "no-list-public", "s852-no-list-public", [
                ("module s852_nolist_public\nimplicit none\npublic", "module s852_nolist_public\nimplicit none\nprivate"),
                ("integer :: no_list_private = 141, explicit_private = 147, imported_default = 153", "integer :: no_list_public = 137, no_list_private = 141, explicit_private = 147, imported_default = 153"),
            ]),
            mg("s852-no-list-private-to-public", "no-list-private-local", "s852-no-list-private-local", [
                ("module s852_nolist_private\nimplicit none\nprivate", "module s852_nolist_private\nimplicit none\npublic"),
                ("integer :: no_list_private = 141, explicit_private = 147, imported_default = 153", "integer :: explicit_private = 147, imported_default = 153"),
            ]),
            mg("s852-explicit-public-to-private", "explicit-identifier-access", "s852-explicit-public-in-private-default", [
                ("public :: explicit_public", "private :: explicit_public"),
                ("integer :: no_list_private = 141, explicit_private = 147, imported_default = 153", "integer :: explicit_public = 143, no_list_private = 141, explicit_private = 147, imported_default = 153"),
            ]),
            mg("s852-explicit-private-to-public", "explicit-identifier-access", "s852-explicit-private-in-public-default", [
                ("private :: explicit_private", "public :: explicit_private"),
                ("integer :: no_list_private = 141, explicit_private = 147, imported_default = 153", "integer :: no_list_private = 141, imported_default = 153"),
            ]),
            mg("s852-import-default-to-public", "use-associated-local-default", "s852-use-associated-local-default", [
                ("module s852_middle_default\nuse s852_origin_default, only: imported_default => origin_default\nimplicit none\nprivate", "module s852_middle_default\nuse s852_origin_default, only: imported_default => origin_default\nimplicit none\npublic"),
                ("integer :: no_list_private = 141, explicit_private = 147, imported_default = 153", "integer :: no_list_private = 141, explicit_private = 147"),
            ]),
        ],
    ))

    s003_source = CHECKS + body(r"""
        module s8523_private_data_provider
        implicit none
        private :: hidden_data
        integer :: hidden_data = 61
        end module s8523_private_data_provider
        module s8523_proc_provider
        implicit none
        private :: hidden_proc, hidden_gen
        interface hidden_gen
          module procedure provider_gen_int
        end interface hidden_gen
        contains
        integer function hidden_proc()
        hidden_proc = 71
        end function hidden_proc
        integer function provider_gen_int(x)
        integer, intent(in) :: x
        provider_gen_int = x + 80
        end function provider_gen_int
        end module s8523_proc_provider
        module s8523_origin
        implicit none
        integer, public :: origin_reexp = 91
        end module s8523_origin
        module s8523_reexport_middle
        use s8523_origin, only: reexp => origin_reexp
        implicit none
        private :: reexp
        end module s8523_reexport_middle
        program p
        use attribute_8_5_checks
        use s8523_private_data_provider
        use s8523_proc_provider
        use s8523_reexport_middle
        implicit none
        integer :: hidden_data = 161, reexp = 171
        interface hidden_gen
          procedure local_gen_int
        end interface hidden_gen
        call check_int('s8523-private-data-name-fallback', hidden_data, 161)
        call check_int('s8523-private-procedure-name-fallback', hidden_proc(), 191)
        call check_int('s8523-private-generic-identifier-fallback', hidden_gen(5), 205)
        call check_int('s8523-private-reexport-fallback', reexp, 171)
        call finish_checks(4)
        contains
        integer function hidden_proc()
        hidden_proc = 191
        end function hidden_proc
        integer function local_gen_int(x)
        integer, intent(in) :: x
        local_gen_int = x + 200
        end function local_gen_int
        end program p
    """)
    specs.append(dict(
        id=f"{TOPIC}_s852_private_use_resolution",
        rule="S8.5.2-003",
        facets=["private-data-name", "private-procedure-name", "private-generic-identifier", "private-reexport"],
        evidence="positive-control",
        source=s003_source,
        checks=4,
        derivation="8.5.2 p4 allows use association only for identifiers PUBLIC in the exporting module; private data, procedure, generic and re-exported identifiers therefore resolve to distinct local sentinels.",
        mutants=[
            mg("s8523-private-data-public", "private-data-name", "s8523-private-data-name-fallback", [
                ("private :: hidden_data", "public :: hidden_data"),
                ("integer :: hidden_data = 161, reexp = 171", "integer :: reexp = 171"),
            ]),
            mg("s8523-private-procedure-public", "private-procedure-name", "s8523-private-procedure-name-fallback", [
                ("private :: hidden_proc, hidden_gen", "public :: hidden_proc\nprivate :: hidden_gen"),
                ("integer function hidden_proc()\nhidden_proc = 191\nend function hidden_proc\ninteger function local_gen_int", "integer function local_gen_int"),
            ]),
            mg("s8523-private-generic-public", "private-generic-identifier", "s8523-private-generic-identifier-fallback", [
                ("private :: hidden_proc, hidden_gen", "private :: hidden_proc\npublic :: hidden_gen"),
                ("interface hidden_gen\n  procedure local_gen_int\nend interface hidden_gen", "! local hidden_gen generic removed"),
            ]),
            mg("s8523-reexport-public", "private-reexport", "s8523-private-reexport-fallback", [
                ("private :: reexp", "public :: reexp"),
                ("integer :: hidden_data = 161, reexp = 171", "integer :: hidden_data = 161"),
            ]),
        ],
    ))
    return {spec["id"]: spec for spec in specs}


def build_corpus(root=ROOT):
    specs = build_specs()
    files = {}
    for spec in specs.values():
        directory = root / case_dir(spec["id"])
        spec["source_path"] = case_dir(spec["id"]) + "/source.f90"
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = manifest(spec).encode("ascii")
    return files, specs


def strip_impl(text):
    return text.split("\n\n" + MARKER, 1)[0].rstrip()


def synced_catalogue(section, catalogue, specs):
    result = json.loads(json.dumps(catalogue))
    by_rule = {}
    for spec in specs.values():
        by_rule.setdefault(spec["rule"], []).append(spec)
    for req in result["requirements"]:
        selected = by_rule.get(req["id"], [])
        if not selected:
            continue
        covered = []
        for spec in selected:
            covered.extend(spec["facets"])
        for facet in covered:
            req["pending"].pop(facet, None)
        if set(req["pending"]) != set(req["facets"]) - set(covered):
            raise ValueError(f"{req['id']}: pending mismatch after fixture sync")
        details = []
        for spec in selected:
            details.append(f"`{spec['id']}` covers " + ", ".join(f"`{f}`" for f in spec["facets"]) + f" with {spec['checks']} run-time assertion(s)")
        paragraph = (MARKER + " " + "; ".join(details) + ". Each assertion has at least one conforming feature mutation that compiles and fails at run time on both checked toolchains. Oracles use only exact INTEGER values, LOGICAL results of direct inquiry expressions, and same-named sentinel resolution; no processor-dependent diagnostic text, file-system effect or timing behavior is asserted.")
        req["oracle"] = strip_impl(req.get("oracle", "")) + "\n\n" + paragraph
        remain = len(req["pending"])
        req["oracle_limitation"] = strip_impl(req.get("oracle_limitation", "")) + (
            f"\n\n{MARKER} {len(covered)} facet(s) are fixture-backed here and {remain} remain pending. "
            "The fixtures do not grant source-use inventory credit, do not cover enumeration accessibility, C817 invalid nonmodule contexts, vector-bound C816 negatives, ASYNCHRONOUS pending-I/O obligations, or associated component/binding owner rules beyond the named facets.")
    return result


def render_view(section, catalogue):
    path = ROOT / VIEWS[section]
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {section} -->", f"<!-- END GENERATED {section} -->"
    if begin not in text or end not in text:
        raise ValueError(f"{VIEWS[section]} lacks generated boundaries")
    prefix = text.split(begin, 1)[0]
    suffix = text.split(end, 1)[1]
    if section == "8.5.1":
        prefix = prefix.replace("twenty facets: six represented,\nand fourteen pending", "twenty facets: eight represented,\nand twelve pending")
    if section == "8.5.2":
        prefix = prefix.replace("**Accessibility source plans.** All thirty-five finite plans remain pending.",
                                "**Accessibility fixtures.** Fourteen finite plans are fixture-backed here and twenty-one remain pending.")
        prefix = prefix.replace("It adds no accessibility execution or SourceUses instance.",
                                "It adds fixture-backed accessibility execution for the named facets, but no SourceUses instance.")
        prefix = prefix.replace("Five requirements have thirty-five facets, all pending.",
                                "Five requirements have thirty-five facets: fourteen represented and twenty-one pending.")
        prefix = prefix.replace("and canonical-witness plans remain in the catalogue, not in new evidence\nregistry instances.",
                                "and canonical-witness plans remain in the catalogue; represented facets name their fixture assertions below.")
    content = "\n".join(render_requirement(req) for req in catalogue["requirements"])
    return prefix + begin + "\n\n" + content + "\n" + end + suffix.rstrip() + "\n"


def sync_files(files, specs):
    for path, raw in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    for section, rel in CATALOGUES.items():
        path = ROOT / rel
        current = json.loads(path.read_text())
        updated = synced_catalogue(section, current, specs)
        path.write_text(json.dumps(updated, indent=2) + "\n")
        (ROOT / VIEWS[section]).write_text(render_view(section, updated))


def check_files(files, specs):
    stale = []
    for path, raw in files.items():
        if not path.is_file() or path.read_bytes() != raw:
            stale.append(str(path.relative_to(ROOT)))
    actual = {p for p in (ROOT / "tests/fixtures").glob(TOPIC + "_*/*") if p.is_file()}
    stale += [str(p.relative_to(ROOT)) for p in sorted(actual - set(files))]
    for section, rel in CATALOGUES.items():
        path = ROOT / rel
        current = json.loads(path.read_text())
        expected = synced_catalogue(section, current, specs)
        if current != expected:
            stale.append(rel)
        view = render_view(section, expected)
        if not (ROOT / VIEWS[section]).is_file() or (ROOT / VIEWS[section]).read_text() != view:
            stale.append(VIEWS[section])
    if stale:
        raise SystemExit("stale attributes_8_5_1_8_5_4 packet: " + ", ".join(sorted(stale)))


def compiler_command(compiler, std):
    name = Path(compiler).name.lower()
    if "lfortran" in name:
        return [compiler, f"--std={std}"]
    return [compiler, f"-std={std}"]


def run_mutations(compiler, std, keep=False):
    _, specs = build_corpus(ROOT)
    digest = hashlib.sha256((compiler + "\0" + std).encode()).hexdigest()[:12]
    base = ROOT / f".mutation_{TOPIC}" / digest
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    total = 0
    try:
        for name, spec in specs.items():
            parent = (ROOT / spec["source_path"]).read_text()
            by_facet = set()
            for mutant in spec["mutants"]:
                total += 1
                by_facet.add(mutant["facet"])
                mutated = parent
                changes = mutant["changes"] if "changes" in mutant else [dict(old=mutant["old"], new=mutant["new"])]
                for change in changes:
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
                                       text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=40)
                if built.returncode != 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant failed to compile\n{built.stdout}")
                ran = subprocess.run([str(exe)], cwd=work, text=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, timeout=40)
                if ran.returncode == 0:
                    raise SystemExit(f"{name}/{mutant['id']}: mutant survived")
            if by_facet != set(spec["facets"]):
                raise SystemExit(f"{name}: facets without mutants {sorted(set(spec['facets']) - by_facet)}")
        print(f"Mutation check failed all {total} mutants with {compiler} ({std}).")
    finally:
        if keep:
            print(f"Kept mutation work in {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)
            if base.parent.exists() and not any(base.parent.iterdir()):
                base.parent.rmdir()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--mutation-check", action="store_true")
    parser.add_argument("--compiler")
    parser.add_argument("--std", default="f2023")
    parser.add_argument("--keep-mutation-work", action="store_true")
    args = parser.parse_args()
    if args.mutation_check:
        if not args.compiler:
            parser.error("--mutation-check requires --compiler")
        run_mutations(args.compiler, args.std, args.keep_mutation_work)
        return
    files, specs = build_corpus(ROOT)
    if args.check:
        check_files(files, specs)
        action = "Checked"
    else:
        sync_files(files, specs)
        action = "Generated"
    print(f"{action} {len(files)} files for {len(specs)} fixtures and {sum(len(s['facets']) for s in specs.values())} facets.")


if __name__ == "__main__":
    main()
