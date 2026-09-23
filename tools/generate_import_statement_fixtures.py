#!/usr/bin/env python3
"""Executable and diagnostic fixtures for Fortran 2023 IMPORT statements."""

import argparse
import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import sys

from generate_assumed_rank_effect_fixtures import owned_paragraph

ROOT = Path(__file__).resolve().parents[1]
SECTION = "8.8"
CATALOGUE = "doc/catalogues/import_statement_8_8.json"
VIEW = "doc/fortran_2023_8_8.md"
SUMMARY_BEGIN = "<!-- BEGIN IMPORT STATEMENT FIXTURES -->"
SUMMARY_END = "<!-- END IMPORT STATEMENT FIXTURES -->"

EXCLUSIONS = (
    "not implemented", "not yet implemented", "unimplemented", "unsupported", "not supported",
    "internal:", "internal error", "asr", "verifier", "out of memory", "segmentation fault",
    "stack trace", "please report unclear",
)

SELECTED = {
    "R870": [
        "bare-form", "basic-list-no-colon", "basic-list-double-colon",
        "basic-multiple-names", "only-required-list", "none-form", "all-form",
    ],
    "C8100": [
        "main-program-exclusion", "external-subprogram-exclusion",
        "module-exclusion", "block-data-exclusion",
    ],
    "C8104": ["same-scope-and-single-controls"],
    "S8.8-001": [
        "listed-name-union", "unlisted-host-name-exclusion", "independent-use-and-local-routes",
    ],
    "S8.8-003": ["explicit-none-host-exclusion", "independent-use-and-local-control"],
    "S8.8-005": ["actual-host-value-observation"],
    "S8.8-006": ["bare-host-value-observation"],
    "S8.8-007": ["ordinary-interface-type-availability"],
}
EFFECT_RULES = {"S8.8-005", "S8.8-006", "S8.8-007"}

COMPLETIONS = {
    "forms": "IMPORT STATEMENT FORMS OK\n",
    "only": "IMPORT STATEMENT ONLY OK\n",
    "none": "IMPORT STATEMENT NONE OK\n",
    "all": "IMPORT STATEMENT ALL OK\n",
    "bare": "IMPORT STATEMENT BARE OK\n",
    "interface": "IMPORT STATEMENT INTERFACE OK\n",
    "c8104_single_controls": "IMPORT STATEMENT C8104 SINGLE CONTROLS OK\n",
    "main_control": "IMPORT STATEMENT C8100 MAIN CONTROL OK\n",
    "external_control": "IMPORT STATEMENT C8100 EXTERNAL CONTROL OK\n",
    "module_control": "IMPORT STATEMENT C8100 MODULE CONTROL OK\n",
    "block_data_control": "IMPORT STATEMENT C8100 BLOCK DATA CONTROL OK\n",
}

C8100_GFORTRAN = (
    "F2018: C897 IMPORT statement at (1) cannot appear in a main program, "
    "an external subprogram, a module or block data"
)
C8100_CAUSES = {
    "main": [
        C8100_GFORTRAN,
        "syntax error: import statement is not allowed in a main program",
        "import statement is not allowed in a main program",
    ],
    "external": [
        C8100_GFORTRAN,
        "syntax error: import statement is not allowed in an external subprogram",
        "import statement is not allowed in an external subprogram",
    ],
    "module": [
        C8100_GFORTRAN,
        "syntax error: import statement is not allowed in a module",
        "import statement is not allowed in a module",
    ],
    "block_data": [
        C8100_GFORTRAN,
        "syntax error: import statement is not allowed in a block data",
        "import statement is not allowed in a block data",
    ],
}

ORACLE_PREFIXES = {
    "R870": "R870 executable syntax-form fixtures: ",
    "C8100": "C8100 top-level exclusion diagnostic fixtures: ",
    "S8.8-001": "S8.8-001 ONLY host-access runtime fixture: ",
    "S8.8-003": "S8.8-003 NONE host-access runtime fixture: ",
    "C8104": "C8104 single NONE/ALL positive-control fixture: ",
    "S8.8-005": "S8.8-005 ALL host-access runtime fixture: ",
    "S8.8-006": "S8.8-006 bare IMPORT host-access runtime fixture: ",
    "S8.8-007": "S8.8-007 interface-body listed IMPORT fixture: ",
}
LIMIT_PREFIXES = {
    rule: text.replace("fixtures: ", "boundaries: ").replace("fixture: ", "boundaries: ")
    for rule, text in ORACLE_PREFIXES.items()
}
ORACLES = {
    "R870": ORACLE_PREFIXES["R870"] + (
        "one complete run/positive-control/f2023 program contains a bare IMPORT, a basic "
        "IMPORT name with no double colon, a basic IMPORT :: list containing two names, two "
        "IMPORT, ONLY: statements with required nonempty lists, one IMPORT, NONE, and one "
        "IMPORT, ALL in distinct eligible internal scoping units. Each subprogram returns a "
        "checked nonzero value or host-state effect before the program emits its completion "
        "line, so the syntax admissions are not empty compile-only parses."
    ),
    "C8100": ORACLE_PREFIXES["C8100"] + (
        "four compile/diagnose negatives place a bare IMPORT as the only selected defect in "
        "the scoping unit of a main program, external subroutine, module, or block data program "
        "unit. The paired controls delete exactly that IMPORT statement and otherwise keep the "
        "same complete source; each control links and runs, observing a nonzero value. The "
        "diagnostic must be located on the IMPORT line and must not be an unsupported-feature, "
        "internal-compiler, source-echo, or crash report. The external-subprogram case exposes "
        "a frozen LFortran acceptance defect; gfortran diagnoses it under the pinned text."
    ),
    "S8.8-001": ORACLE_PREFIXES["S8.8-001"] + (
        "one internal subroutine has two IMPORT, ONLY: statements that import host integers hx "
        "and hy. A same-spelled host hz is deliberately not in either list; the subroutine "
        "declares its own local hz, assigns it the nonzero value 7, and returns hx+hy+hz = 18. "
        "The host hz starts at 100 and is checked unchanged after the call. A conforming feature "
        "mutation adds hz to an ONLY list and removes the compensating local declaration, which "
        "keeps the program valid but changes the host hz to 7 and fails the host-state check."
    ),
    "S8.8-003": ORACLE_PREFIXES["S8.8-003"] + (
        "one internal subroutine begins with IMPORT, NONE, declares its own local hz, assigns "
        "that local value 7, and returns it while the host hz remains the nonzero sentinel 100. "
        "The feature mutation replaces NONE by ALL and removes the local declaration, so the "
        "same assignment reaches the host object and the caller's unchanged-host check fails."
    ),
    "C8104": ORACLE_PREFIXES["C8104"] + (
        "one complete run/positive-control/f2023 source contains a single IMPORT, NONE in one "
        "internal subroutine and a single IMPORT, ALL in a different internal subroutine. No "
        "scoping unit contains a second IMPORT statement alongside either form. Both scopes are "
        "called and checked with nonzero values, so the control proves the single-statement "
        "premise without relying on a no-op compile admission."
    ),
    "S8.8-005": ORACLE_PREFIXES["S8.8-005"] + (
        "one internal subroutine begins with IMPORT, ALL and uses two host integers: hx remains "
        "5, hz is updated from 100 to 7, and the returned sum hx+hz is 12. The feature mutation "
        "narrows the import to ONLY: hx and inserts a compensating local hz declaration, so the "
        "program remains conforming while the required host update disappears."
    ),
    "S8.8-006": ORACLE_PREFIXES["S8.8-006"] + (
        "one internal subroutine uses bare IMPORT to access host hx and hz, assigns hz = 6, "
        "returns hx+hz = 11, and the caller observes the host hz changed to 6. The feature "
        "mutation narrows access to ONLY: hx and inserts a local hz declaration, keeping the "
        "mutant conforming while making the host-state oracle fail."
    ),
    "S8.8-007": ORACLE_PREFIXES["S8.8-007"] + (
        "one module procedure contains an ordinary interface body for external subroutine "
        "monitor. IMPORT :: box, rk, slot_count makes the prior host derived type, kind "
        "parameter and named constant available for the dummy declarations. A call through "
        "that explicit interface passes two box values, 31_rk and 11_rk; the external "
        "procedure sums the explicit-shape dummy and returns 42_rk, which the main program "
        "checks at run time."
    ),
}
LIMITATIONS = {
    "R870": LIMIT_PREFIXES["R870"] + (
        "only the seven selected positive form facets are covered. Empty lists, malformed "
        "punctuation, designators, renames, generic syntax, source-order mapping, and numbered "
        "syntax diagnostics remain pending."
    ),
    "C8100": LIMIT_PREFIXES["C8100"] + (
        "only bare IMPORT exclusions in four top-level scoping-unit categories are covered. "
        "Nested eligible scopes, submodule contexts, derived-type grammar, and other constraints "
        "remain pending. Block data and COMMON are used only to make the deletion control run."
    ),
    "S8.8-001": LIMIT_PREFIXES["S8.8-001"] + (
        "only a non-BLOCK internal subprogram with two ONLY lists, imported integer objects, "
        "and one explicit local same-spelled object is covered. BLOCK-only rules, USE routes, "
        "intrinsic names, and nested host graphs remain pending."
    ),
    "S8.8-003": LIMIT_PREFIXES["S8.8-003"] + (
        "only explicit IMPORT, NONE in an internal subprogram and a separate explicitly declared "
        "local integer are covered. Ordinary-interface default NONE, module-procedure interface "
        "boundaries, implicit typing, and independent USE routes remain pending."
    ),
    "C8104": LIMIT_PREFIXES["C8104"] + (
        "only the positive single-statement side of C8104 is covered. Repeated NONE, repeated "
        "ALL, mixed NONE/ALL, companions with other IMPORT forms, and same-scope diagnostics "
        "remain pending."
    ),
    "S8.8-005": LIMIT_PREFIXES["S8.8-005"] + (
        "only two ordinary host integer variables in an internal subprogram are covered. Other "
        "host entity classes, BLOCK scopes, and C8106 no-hiding negatives remain pending."
    ),
    "S8.8-006": LIMIT_PREFIXES["S8.8-006"] + (
        "only explicit bare IMPORT in an internal subprogram is covered. Default host access in "
        "scopes with no IMPORT, legitimate local-shadow controls, derived-type definitions, "
        "module procedure interface bodies, module subprograms, and submodules remain pending."
    ),
    "S8.8-007": LIMIT_PREFIXES["S8.8-007"] + (
        "only a prior module type, kind parameter and integer named constant imported into one "
        "ordinary interface body are covered. Multiple basic lists, USE-renamed host names, "
        "BLOCK behavior, opaque PRIVATE representation, and full source graph inventory remain "
        "pending."
    ),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def ident(name):
    return "import_statement_" + name


def _replace_all(text, replacements):
    for expected, replacement in replacements:
        if text.count(expected) != 1:
            raise ValueError(f"mutation token count changed for {expected!r}: {text.count(expected)}")
        text = text.replace(expected, replacement)
    return text


def _line_of(text, token):
    return text[:text.index(token)].count("\n") + 1


def run_program_source(variant, rule, facets, source, *, mutations):
    raw = source.encode("ascii")
    return dict(
        id=ident(variant), variant=variant, kind="valid",
        evidence="effect" if rule in EFFECT_RULES else "positive-control",
        rule=rule, facets=list(facets), phase="run", source=source, source_sha256=sha(raw),
        completion=COMPLETIONS[variant], feature_mutations=mutations, oracle_mutations=[
            dict(id="completion-text", replacements=[[COMPLETIONS[variant].rstrip("\n"), "IMPORT STATEMENT BAD"]],
                 conforming=True),
        ],
        input_mutations=[], line_derivation="Runtime checks derive from Fortran 2023 8.8 host accessibility.")


def forms_source():
    return """program import_statement_forms
  implicit none
  integer :: host_a, host_b, host_c, observed
  host_a = 2
  host_b = 3
  host_c = 40
  observed = -77
  call bare_case(observed)
  if (observed /= 6) error stop 1
  if (host_c /= 4) error stop 2
  host_c = 40
  call basic_case(observed)
  if (observed /= 45) error stop 3
  call only_case(observed)
  if (observed /= 12) error stop 4
  if (host_c /= 40) error stop 5
  call none_case(observed)
  if (observed /= 8) error stop 6
  if (host_c /= 40) error stop 7
  call all_case(observed)
  if (observed /= 11) error stop 8
  if (host_c /= 6) error stop 9
  write(*,'(a)') 'IMPORT STATEMENT FORMS OK'
contains
  subroutine bare_case(out)
    import
    integer, intent(out) :: out
    host_c = 4
    out = host_a + host_c
  end subroutine
  subroutine basic_case(out)
    import host_a
    import :: host_b, host_c
    integer, intent(out) :: out
    out = host_a + host_b + host_c
  end subroutine
  subroutine only_case(out)
    import, only: host_a
    import, only: host_b
    integer, intent(out) :: out
    integer :: host_c
    host_c = 7
    out = host_a + host_b + host_c
  end subroutine
  subroutine none_case(out)
    import, none
    integer, intent(out) :: out
    integer :: host_c
    host_c = 8
    out = host_c
  end subroutine
  subroutine all_case(out)
    import, all
    integer, intent(out) :: out
    host_c = 6
    out = host_a + host_b + host_c
  end subroutine
end program import_statement_forms
"""


def only_source():
    return """program import_statement_only_effect
  implicit none
  integer :: hx, hy, hz, observed
  hx = 5
  hy = 6
  hz = 100
  observed = -77
  call inner(observed)
  if (observed /= 18) error stop 1
  if (hz /= 100) error stop 2
  write(*,'(a)') 'IMPORT STATEMENT ONLY OK'
contains
  subroutine inner(out)
    import, only: hx
    import, only: hy
    integer, intent(out) :: out
    integer :: hz
    hz = 7
    out = hx + hy + hz
  end subroutine
end program import_statement_only_effect
"""


def none_source():
    return """program import_statement_none_effect
  implicit none
  integer :: hz, observed
  hz = 100
  observed = -77
  call inner(observed)
  if (observed /= 7) error stop 1
  if (hz /= 100) error stop 2
  write(*,'(a)') 'IMPORT STATEMENT NONE OK'
contains
  subroutine inner(out)
    import, none
    integer, intent(out) :: out
    integer :: hz
    hz = 7
    out = hz
  end subroutine
end program import_statement_none_effect
"""


def all_source():
    return """program import_statement_all_effect
  implicit none
  integer :: hx, hz, observed
  hx = 5
  hz = 100
  observed = -77
  call inner(observed)
  if (observed /= 12) error stop 1
  if (hz /= 7) error stop 2
  write(*,'(a)') 'IMPORT STATEMENT ALL OK'
contains
  subroutine inner(out)
    import, all
    integer, intent(out) :: out
    hz = 7
    out = hx + hz
  end subroutine
end program import_statement_all_effect
"""


def bare_source():
    return """program import_statement_bare_effect
  implicit none
  integer :: hx, hz, observed
  hx = 5
  hz = 100
  observed = -77
  call inner(observed)
  if (observed /= 11) error stop 1
  if (hz /= 6) error stop 2
  write(*,'(a)') 'IMPORT STATEMENT BARE OK'
contains
  subroutine inner(out)
    import
    integer, intent(out) :: out
    hz = 6
    out = hx + hz
  end subroutine
end program import_statement_bare_effect
"""


def interface_source():
    return """module import_statement_interface_support
  implicit none
  integer, parameter :: rk = selected_int_kind(9)
  integer, parameter :: slot_count = 2
  integer, parameter :: slot_count_alt = 1
  type :: box
    integer(rk) :: value
  end type
contains
  subroutine run_interface(observed)
    integer(rk), intent(out) :: observed
    interface
      subroutine monitor(item, answer)
        import :: box, rk, slot_count
        type(box), intent(in) :: item(slot_count)
        integer(rk), intent(out) :: answer
      end subroutine
    end interface
    type(box) :: payload(slot_count)
    payload(1)%value = 31_rk
    payload(2)%value = 11_rk
    observed = -77_rk
    call monitor(payload, observed)
  end subroutine
end module import_statement_interface_support

subroutine monitor(item, answer)
  use import_statement_interface_support, only: box, rk, slot_count
  implicit none
  type(box), intent(in) :: item(slot_count)
  integer(rk), intent(out) :: answer
  integer :: i
  answer = 0_rk
  do i = 1, size(item)
    answer = answer + item(i)%value
  end do
end subroutine monitor

program import_statement_interface_effect
  use import_statement_interface_support, only: rk, run_interface
  implicit none
  integer(rk) :: observed
  observed = -99_rk
  call run_interface(observed)
  if (observed /= 42_rk) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT INTERFACE OK'
end program import_statement_interface_effect
"""


def c8100_sources():
    controls = {
        "main": """program import_statement_c8100_main
  implicit none
  integer :: value
  value = 31
  if (value /= 31) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT C8100 MAIN CONTROL OK'
end program import_statement_c8100_main
""",
        "external": """subroutine import_statement_c8100_external(value)
  implicit none
  integer, intent(out) :: value
  value = 37
end subroutine import_statement_c8100_external

program import_statement_c8100_external_control
  implicit none
  integer :: value
  value = -77
  call import_statement_c8100_external(value)
  if (value /= 37) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT C8100 EXTERNAL CONTROL OK'
end program import_statement_c8100_external_control
""",
        "module": """module import_statement_c8100_module_scope
  implicit none
  integer, parameter :: value = 41
end module import_statement_c8100_module_scope

program import_statement_c8100_module_control
  use import_statement_c8100_module_scope, only: value
  implicit none
  if (value /= 41) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT C8100 MODULE CONTROL OK'
end program import_statement_c8100_module_control
""",
        "block_data": """block data import_statement_c8100_block_data
  integer :: value
  common /import_statement_c8100_common/ value
  data value /43/
end block data import_statement_c8100_block_data

program import_statement_c8100_block_data_control
  implicit none
  integer :: value
  common /import_statement_c8100_common/ value
  if (value /= 43) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT C8100 BLOCK DATA CONTROL OK'
end program import_statement_c8100_block_data_control
""",
    }
    invalids = {
        "main": controls["main"].replace("program import_statement_c8100_main\n",
                                         "program import_statement_c8100_main\n  import\n", 1),
        "external": controls["external"].replace("subroutine import_statement_c8100_external(value)\n",
                                                 "subroutine import_statement_c8100_external(value)\n  import\n", 1),
        "module": controls["module"].replace("module import_statement_c8100_module_scope\n",
                                             "module import_statement_c8100_module_scope\n  import\n", 1),
        "block_data": controls["block_data"].replace("block data import_statement_c8100_block_data\n",
                                                     "block data import_statement_c8100_block_data\n  import\n", 1),
    }
    return controls, invalids


def build_specs():
    specs = {}
    specs[ident("forms")] = run_program_source(
        "forms", "R870", SELECTED["R870"], forms_source(),
        mutations=[
            dict(id="only-import-host-c", replacements=[
                ["    import, only: host_b\n    integer, intent(out) :: out\n    integer :: host_c\n",
                 "    import, only: host_b, host_c\n    integer, intent(out) :: out\n"],
            ], conforming=True),
            dict(id="none-to-all-host-c", replacements=[
                ["    import, none\n    integer, intent(out) :: out\n    integer :: host_c\n",
                 "    import, all\n    integer, intent(out) :: out\n"],
            ], conforming=True),
        ])
    c8104_spec = run_program_source(
        "c8104_single_controls", "C8104", SELECTED["C8104"], forms_source().replace(
            "IMPORT STATEMENT FORMS OK", "IMPORT STATEMENT C8104 SINGLE CONTROLS OK"),
        mutations=[])
    c8104_spec["evidence"] = "positive-control"
    c8104_spec["completion"] = "IMPORT STATEMENT C8104 SINGLE CONTROLS OK\n"
    c8104_spec["oracle_mutations"] = []
    specs[ident("c8104_single_controls")] = c8104_spec
    specs[ident("only")] = run_program_source(
        "only", "S8.8-001", SELECTED["S8.8-001"], only_source(),
        mutations=[dict(id="import-excluded-hz", replacements=[
            ["    import, only: hy\n", "    import, only: hy, hz\n"],
            ["    integer :: hz\n", ""],
        ], conforming=True)])
    specs[ident("none")] = run_program_source(
        "none", "S8.8-003", SELECTED["S8.8-003"], none_source(),
        mutations=[dict(id="none-to-all", replacements=[
            ["    import, none\n", "    import, all\n"],
            ["    integer :: hz\n", ""],
        ], conforming=True)])
    specs[ident("all")] = run_program_source(
        "all", "S8.8-005", SELECTED["S8.8-005"], all_source(),
        mutations=[dict(id="all-to-only-local-hz", replacements=[
            ["    import, all\n", "    import, only: hx\n"],
            ["    integer, intent(out) :: out\n", "    integer, intent(out) :: out\n    integer :: hz\n"],
        ], conforming=True)])
    specs[ident("bare")] = run_program_source(
        "bare", "S8.8-006", SELECTED["S8.8-006"], bare_source(),
        mutations=[dict(id="bare-to-only-local-hz", replacements=[
            ["    import\n", "    import, only: hx\n"],
            ["    integer, intent(out) :: out\n", "    integer, intent(out) :: out\n    integer :: hz\n"],
        ], conforming=True)])
    specs[ident("interface")] = run_program_source(
        "interface", "S8.8-007", SELECTED["S8.8-007"], interface_source(),
        mutations=[dict(id="import-alternate-shape-constant", replacements=[
            ["        import :: box, rk, slot_count\n", "        import :: box, rk, slot_count_alt\n"],
            ["        type(box), intent(in) :: item(slot_count)\n",
             "        type(box), intent(in) :: item(slot_count_alt)\n"],
            ["  use import_statement_interface_support, only: box, rk, slot_count\n",
             "  use import_statement_interface_support, only: box, rk, slot_count_alt\n"],
            ["  type(box), intent(in) :: item(slot_count)\n",
             "  type(box), intent(in) :: item(slot_count_alt)\n"],
        ], conforming=True)])
    controls, invalids = c8100_sources()
    facets = {
        "main": ["main-program-exclusion"],
        "external": ["external-subprogram-exclusion"],
        "module": ["module-exclusion"],
        "block_data": ["block-data-exclusion"],
    }
    for key, source in controls.items():
        variant = key + "_control"
        spec = run_program_source(variant, "C8100", facets[key], source, mutations=[])
        spec["evidence"] = "positive-control"
        spec["control_for"] = ident(key + "_invalid")
        specs[ident(variant)] = spec
    for key, source in invalids.items():
        raw = source.encode("ascii")
        control_id = ident(key + "_control")
        specs[ident(key + "_invalid")] = dict(
            id=ident(key + "_invalid"), variant=key + "_invalid", kind="invalid",
            evidence="effect", rule="C8100", facets=facets[key], phase="compile",
            source=source, source_sha256=sha(raw), control_id=control_id,
            diagnostic=dict(
                file="source.f90", line=_line_of(source, "  import"), end_line=_line_of(source, "  import"),
                contains_any=C8100_CAUSES[key], excludes_any=list(EXCLUSIONS)),
            repair=dict(control_id=control_id, deleted="  import\n",
                        control_sha256=sha(controls[key].encode("ascii"))),
            line_derivation="Fortran 2023 C8100 excludes IMPORT from this top-level scoping unit.")
    return specs


def mutated_source(spec, mutation):
    raw = spec["source"].encode("ascii")
    if sha(raw) != spec["source_sha256"]:
        raise ValueError("the complete parent source no longer matches its fingerprint")
    return _replace_all(spec["source"], mutation["replacements"]).encode("ascii")


def all_mutations(spec):
    return spec.get("feature_mutations", []) + spec.get("oracle_mutations", []) + spec.get("input_mutations", [])


def build_corpus(root=ROOT):
    files, specs = {}, build_specs()
    for spec in specs.values():
        directory = Path(root) / "tests/fixtures" / spec["id"]
        manifest = dict(
            schema_version=1, id=spec["id"], rule=spec["rule"], facets=spec["facets"],
            evidence=spec["evidence"], standard="f2023", files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
        )
        if spec["phase"] == "run":
            manifest["link"] = dict(driver="fortran", objects=["source.o"], output="program")
            manifest["expect"] = dict(
                phase="run", outcome="success", exit_code=0, stdout=spec["completion"], stderr="")
        else:
            manifest["expect"] = dict(
                phase="compile", step="source", outcome="diagnose", diagnostic=spec["diagnostic"])
        spec["path"] = directory.relative_to(root).as_posix() + "/fixture.json"
        spec["manifest"] = manifest
        files[directory / "source.f90"] = spec["source"].encode("ascii")
        files[directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode("ascii")
    return files, specs


def synced_catalogue(catalogue):
    updated = copy.deepcopy(catalogue)
    by_rule = {row["id"]: row for row in updated["requirements"]}
    for rule, facets in SELECTED.items():
        owner = by_rule[rule]
        if not set(facets) <= set(owner["facets"]):
            raise ValueError("selected IMPORT facets changed for " + rule)
        for facet in facets:
            owner["pending"].pop(facet, None)
        owner["oracle"] = owned_paragraph(owner.get("oracle", ""), ORACLE_PREFIXES[rule], ORACLES[rule])
        owner["oracle_limitation"] = owned_paragraph(
            owner.get("oracle_limitation", ""), LIMIT_PREFIXES[rule], LIMITATIONS[rule])
    return updated


def render_view(catalogue, root=ROOT):
    sys.path.insert(0, str(Path(root) / "tests"))
    from suite_data import render_requirement
    path = Path(root) / VIEW
    text = path.read_text()
    begin, end = f"<!-- BEGIN GENERATED {SECTION} -->", f"<!-- END GENERATED {SECTION} -->"
    if text.count(begin) != 1 or text.count(end) != 1:
        raise ValueError("generated-region boundaries changed")
    before, rest = text.split(begin)
    _, after = rest.split(end)
    summary = (
        SUMMARY_BEGIN + "\n"
        "## IMPORT statement executable packet\n\n"
        "Fifteen fixtures cover twenty selected facets of 8.8. Runtime fixtures observe "
        "ONLY, NONE, ALL, bare, and listed IMPORT effects through nonzero integer values "
        "and host-object state, and the R870 form fixture executes every admitted selected "
        "form in eligible internal scopes. The interface-body fixture imports a host derived "
        "type, kind parameter and shape constant into an ordinary interface body, then calls "
        "the declared procedure and checks the returned 42_rk value.\n\n"
        "C8100 diagnostics place bare IMPORT in the scoping unit of a main program, external "
        "subroutine, module, and block data. Each repair deletes exactly that IMPORT and runs "
        "a complete control. Frozen LFortran currently accepts the external-subprogram "
        "negative; the case is retained because gfortran diagnoses it and C8100 requires it.\n\n"
        "Feature mutations are permanent generator data. The ONLY/NONE/ALL/bare mutations "
        "compensate local declarations so the mutants remain conforming and fail at run time "
        "by changing whether hz is the host object or a local object. The interface fixture "
        "has a conforming alternate-shape-constant mutation that compiles and fails at run time; "
        "C8101-C8106, BLOCK, submodule, "
        "ordinary-interface defaults, shadowing negatives, empty-list syntax, and source-graph "
        "inventory not listed in this summary remain pending.\n"
        + SUMMARY_END)
    if SUMMARY_BEGIN in before or SUMMARY_END in before:
        if before.count(SUMMARY_BEGIN) != 1 or before.count(SUMMARY_END) != 1:
            raise ValueError("IMPORT summary boundaries changed")
        leading, owned = before.split(SUMMARY_BEGIN)
        _, trailing = owned.split(SUMMARY_END)
        before = leading + summary + trailing
    else:
        before = before.rstrip() + "\n\n" + summary + "\n\n"
    return before + begin + "\n\n" + "\n".join(render_requirement(row) for row in catalogue["requirements"]) + "\n" + end + after


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
            raise ValueError("stale IMPORT statement fixtures: " + ", ".join(stale))
    else:
        for path, raw in files.items():
            if not path.is_file() or path.read_bytes() != raw:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        if sync_catalogue:
            (root / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (root / VIEW).write_text(view)
    return specs


def _std_flag(compiler, std):
    name = Path(str(compiler)).name.lower()
    return f"--std={std}" if "lfortran" in name else f"-std={std}"


def check_mutations(root, compiler, std):
    root = Path(root).resolve()
    compiler = Path(compiler)
    specs = build_specs()
    mutations = [(spec, mutation) for spec in specs.values() if spec["phase"] == "run" for mutation in all_mutations(spec)]
    if not mutations:
        raise SystemExit("no IMPORT statement mutations defined")
    compile_fail = 0
    run_fail = 0
    survived = []
    with tempfile.TemporaryDirectory(prefix="import_statement_mutations_") as tmp:
        workspace = Path(tmp).resolve()
        for index, (spec, mutation) in enumerate(mutations, 1):
            case_dir = workspace / f"{index:03d}_{spec['variant']}_{mutation['id']}"
            case_dir.mkdir()
            source = case_dir / "source.f90"
            exe = case_dir / "program"
            source.write_bytes(mutated_source(spec, mutation))
            compile_cmd = [str(compiler), _std_flag(compiler, std), str(source.resolve()), "-o", str(exe.resolve())]
            compiled = subprocess.run(compile_cmd, cwd=case_dir, text=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT, timeout=30)
            if compiled.returncode != 0:
                compile_fail += 1
                continue
            run = subprocess.run([str(exe.resolve())], cwd=case_dir, text=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=30)
            if run.returncode != 0 or run.stdout != spec["completion"]:
                run_fail += 1
            else:
                survived.append((spec["id"], mutation["id"], run.stdout))
    total = len(mutations)
    print(f"Mutation check: total={total}, compile_fail={compile_fail}, run_fail={run_fail}, "
          f"survived={len(survived)} for {compiler} ({std}).")
    if compile_fail:
        raise SystemExit("runtime IMPORT mutants must compile; compile_fail=" + str(compile_fail))
    if survived:
        detail = "\n".join(f"{case} {mutation}: {stdout!r}" for case, mutation, stdout in survived)
        raise SystemExit("IMPORT mutation survived:\n" + detail)


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
    selected = sum(len(v) for v in SELECTED.values())
    mutations = sum(len(all_mutations(row)) for row in specs.values())
    print(f"{'Checked' if args.check else 'Generated'} {len(specs)} IMPORT statement cases, "
          f"{selected} facets and {mutations} mutations.")


if __name__ == "__main__":
    main()
