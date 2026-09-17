#!/usr/bin/env python3
"""Two complete BIND-common SAVE runs with an exact two-insertion confirmation."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from generate_bind_variable_placement_fixtures import render_view as placement_view

ROOT = Path(__file__).resolve().parents[1]
RULE = "S8.5.5-002"
CATALOGUE = "doc/catalogues/bind_attribute_data_entities_8_5_5.json"
VIEW = "doc/fortran_2023_8_5_5.md"
FACETS = ("named-common-retention", "explicit-save-confirmation")
COMPLETION = "BIND COMMON SAVE OK\n"
SAVE = "  save /saved_pair/\n"
GUARDS = (
    ("writer-first", "writer_visits", 1),
    ("reader-first", "reader_visits", 1),
    ("left-first", "left_observed", 11),
    ("right-first", "right_observed", 13),
    ("cycle-first", "cycles", 1),
    ("writer-second", "writer_visits", 2),
    ("reader-second", "reader_visits", 2),
    ("left-second", "left_observed", 17),
    ("right-second", "right_observed", 19),
    ("cycle-second", "cycles", 2),
    ("check-total", "checks", 10),
)
ORACLE = (
    "Two complete run/f2023 programs represent only named-common-retention and explicit-save-confirmation. "
    "The effect program's main calls two external procedures through matching complete explicit interfaces. "
    "Only the actual writer and reader declare /saved_pair/, each with two ordinary scalar INTEGER(C_INT) "
    "members in identical order and BIND(C) on the block. Main defines typed inputs11/13, calls the writer "
    "to completion, then calls the reader and checks both returned values against independent literals. "
    "A second complete cycle uses17/19. Main's executable-initialized writer/reader counters are updated "
    "inside the corresponding procedures; four visit checks precede value reads, two cycle checks and "
    "a ten-check completion guard reject missing visits/checks. Eleven scalar guards plus the exact "
    "stdout 'BIND COMMON SAVE OK\\n', empty stderr and normal exit0 constitute the run contract. "
    "The positive-control program differs only by one inserted SAVE /saved_pair/ in each of the two "
    "common-declaring scopes. Original8.5.5p3 expressly permits that confirmation; only its facet is "
    "designated positive_control_facets, not effect evidence. Full-program one-span wrong-oracle probes "
    "target every guard and the completion literal, using only processors that actually execute the current parent."
)
LIMITATION = (
    "The three member-save-source-use, consistent-common-labels and module-variable-save-distinction facets "
    "remain pending; all six other8.5.5requirements are preserved. Main, modules and interface bodies declare "
    "no common storage. Neither program has declaration/DATA/default initialization, pointer, allocatable, "
    "coarray, equivalence, extra common scope or member BIND/SAVE. The effect source has no explicit SAVE; "
    "the control has exactly two block SAVE confirmations, never duplicate or member SAVE. "
    "Both scopes use the same default binding label and type/order/size; C_INT is guaranteed and imported "
    "in each actual/interface scope. Writer assignments define both members before the first read; SAVE "
    "preserves their definition/value across complete returns. Counter actuals are defined and distinct, "
    "and reader OUT actuals are assigned before any use. No unsaved negative, undefined-value trap, physical "
    "static-allocation/address oracle, guessed kind/width, C counterpart or ABI/linkage claim is supplied. "
    "The build links only Fortran program units. Normal-zero exit is the existing observation convention; "
    "ERROR STOP token/status behavior is qualified empirically, not a mandated numeric exit policy. "
    "Compilation/link failures do not qualify runtime sensitivity; actual unsupported/resource/runtime "
    "failures remain failures. Source, fixture, mode-qualified observations and inventory approval are "
    "separate. Generation changes no review, baseline, source-use or canonical-link record."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(variant):
    return "S8_5_5_002_valid__bind_common_save_" + variant


def effect_source():
    source = (
        "program bind_common_retention\n"
        "  use, intrinsic :: iso_c_binding, only: c_int\n"
        "  implicit none\n"
        "  interface\n"
        "    subroutine store_pair(left_value, right_value, visits)\n"
        "      use, intrinsic :: iso_c_binding, only: c_int\n"
        "      implicit none\n"
        "      integer(c_int), intent(in) :: left_value, right_value\n"
        "      integer(c_int), intent(inout) :: visits\n"
        "    end subroutine store_pair\n"
        "    subroutine load_pair(left_value, right_value, visits)\n"
        "      use, intrinsic :: iso_c_binding, only: c_int\n"
        "      implicit none\n"
        "      integer(c_int), intent(out) :: left_value, right_value\n"
        "      integer(c_int), intent(inout) :: visits\n"
        "    end subroutine load_pair\n"
        "  end interface\n"
        "  integer(c_int) :: left_input, right_input, left_observed, right_observed\n"
        "  integer(c_int) :: writer_visits, reader_visits, checks, cycles\n"
        "  writer_visits=0_c_int\n"
        "  reader_visits=0_c_int\n"
        "  checks=0_c_int\n"
        "  cycles=0_c_int\n")
    for cycle, (left, right) in enumerate(((11, 13), (17, 19))):
        source += (f"  left_input={left}_c_int\n  right_input={right}_c_int\n"
                   "  call store_pair(left_input, right_input, writer_visits)\n")
        guards = GUARDS[cycle * 5:cycle * 5 + 5]
        for index, (label, expression, expected) in enumerate(guards):
            if index == 1:
                source += "  call load_pair(left_observed, right_observed, reader_visits)\n"
            if index == 4:
                source += "  cycles=cycles+1_c_int\n"
            source += f"  if ({expression} /= {expected}_c_int) error stop 'BCS:{label}'\n"
            source += "  checks=checks+1_c_int\n"
    source += (
        "  if (checks /= 10_c_int) error stop 'BCS:check-total'\n"
        "  write(*,'(a)') 'BIND COMMON SAVE OK'\n"
        "end program bind_common_retention\n"
        "\n"
        "subroutine store_pair(left_value, right_value, visits)\n"
        "  use, intrinsic :: iso_c_binding, only: c_int\n"
        "  implicit none\n"
        "  integer(c_int), intent(in) :: left_value, right_value\n"
        "  integer(c_int), intent(inout) :: visits\n"
        "  integer(c_int) :: first, second\n"
        "  common /saved_pair/ first, second\n"
        "  bind(c) :: /saved_pair/\n"
        "  first=left_value\n"
        "  second=right_value\n"
        "  visits=visits+1_c_int\n"
        "end subroutine store_pair\n"
        "\n"
        "subroutine load_pair(left_value, right_value, visits)\n"
        "  use, intrinsic :: iso_c_binding, only: c_int\n"
        "  implicit none\n"
        "  integer(c_int), intent(out) :: left_value, right_value\n"
        "  integer(c_int), intent(inout) :: visits\n"
        "  integer(c_int) :: first, second\n"
        "  common /saved_pair/ first, second\n"
        "  bind(c) :: /saved_pair/\n"
        "  left_value=first\n"
        "  right_value=second\n"
        "  visits=visits+1_c_int\n"
        "end subroutine load_pair\n")
    return source


def source_specs():
    original = effect_source().encode("ascii")
    binding = b"  bind(c) :: /saved_pair/\n"
    starts = []
    start = 0
    while (position := original.find(binding, start)) >= 0:
        starts.append(position + len(binding))
        start = position + len(binding)
    if len(starts) != 2:
        raise ValueError("exactly two actual COMMON/BIND scopes are required")
    saved = SAVE.encode()
    confirmation = original
    for position in reversed(starts):
        confirmation = confirmation[:position] + saved + confirmation[position:]
    insertions = [dict(original_byte_offset=position,
                       control_byte_span=[position + index * len(saved), position + (index + 1) * len(saved)],
                       inserted=SAVE, scope=("store_pair", "load_pair")[index])
                  for index, position in enumerate(starts)]
    result = {}
    for variant, facet, role, raw in (
            ("retention", FACETS[0], "effect", original),
            ("confirmation", FACETS[1], "positive-control", confirmation)):
        name = identifier(variant)
        guards = []
        for label, expression, expected in GUARDS:
            statement = f"  if ({expression} /= {expected}_c_int) error stop 'BCS:{label}'"
            encoded = statement.encode()
            if raw.count(encoded) != 1:
                raise ValueError("each scalar guard must identify exactly one complete statement")
            start = raw.index(encoded) + statement.index(f"{expected}_c_int")
            stop = start + len(f"{expected}_c_int")
            guards.append(dict(id=label, expression=expression, expected=expected,
                               literal=f"{expected}_c_int", replacement=f"{expected + 1}_c_int",
                               span=[start, stop], line=raw[:start].count(b"\n") + 1,
                               failure_token="BCS:" + label, kind="guard"))
        literal = b"BIND COMMON SAVE OK"
        start = raw.index(literal)
        guards.append(dict(id="completion-output", kind="output", literal=literal.decode(),
                           replacement="BIND COMMON SAVE BAD", span=[start, start + len(literal)],
                           line=raw[:start].count(b"\n") + 1))
        result[name] = dict(id=name, variant=variant, facet=facet, evidence=role, standard="f2023",
                            phase="run", source=raw.decode(), source_sha256=sha(raw),
                            guards=guards, confirmation_insertions=insertions)
    return result


def wrong_oracle_source(spec, guard):
    raw = spec["source"].encode("ascii")
    start, end = guard["span"]
    if raw[start:end].decode() != guard["literal"]:
        raise ValueError("the oracle mutation no longer binds the complete original source")
    return raw[:start] + guard["replacement"].encode("ascii") + raw[end:]


def build_corpus(root=ROOT):
    files, specs = {}, source_specs()
    for name, spec in specs.items():
        directory = "tests/fixtures/bind_common_save_" + spec["variant"]
        manifest = dict(
            schema_version=1, id=name, rule=RULE, facets=[spec["facet"]], standard="f2023",
            evidence=spec["evidence"], files=["source.f90"],
            build=[dict(id="source", source="source.f90", language="fortran", form="free", output="source.o")],
            link=dict(driver="fortran", objects=["source.o"], output="program"),
            expect=dict(phase="run", outcome="success", exit_code=0, stdout=COMPLETION, stderr=""))
        spec["path"] = directory + "/fixture.json"
        spec["manifest"] = manifest
        files[Path(root) / directory / "source.f90"] = spec["source"].encode("ascii")
        files[Path(root) / directory / "fixture.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files, specs


def synced_catalogue(catalogue):
    result = copy.deepcopy(catalogue)
    requirement = next(row for row in result["requirements"] if row["id"] == RULE)
    for facet in FACETS:
        requirement["pending"].pop(facet, None)
    if set(requirement["pending"]) != set(requirement["facets"]) - set(FACETS):
        raise ValueError("unselected BIND-common SAVE plans must remain pending")
    requirement["positive_control_facets"] = ["explicit-save-confirmation"]
    requirement["oracle"] = ORACLE
    requirement["oracle_limitation"] = LIMITATION
    return result


def render_view(catalogue, root=ROOT):
    text = placement_view(catalogue, root)
    begin, end = "<!-- BEGIN BIND COMMON SAVE -->", "<!-- END BIND COMMON SAVE -->"
    if begin in text or end in text:
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError("invalid BIND-common SAVE view boundaries")
        before, rest = text.split(begin)
        _, after = rest.split(end)
    else:
        before, after = text.rstrip() + "\n\n", "\n"
    requirement = next(row for row in catalogue["requirements"] if row["id"] == RULE)
    section = (
        "## Bounded BIND-common SAVE runs\n\n"
        "Two complete executable programs share one main and two external procedure definitions.\n"
        "Only the writer and reader declare the two-member INTEGER(C_INT) named common block.\n"
        "BIND(C) applies to that block, never its individual members. Matching explicit\n"
        "interfaces import C_INT but do not declare common storage. The writer returns\n"
        "before the reader is called: independent literal checks observe11/13, then17/19.\n\n"
        "Four procedure-visit checks, four returned-value checks, two cycle checks and\n"
        "one ten-check completion guard precede the exact `BIND COMMON SAVE OK` output.\n"
        "All observer counters are initialized by executable statements in main; no\n"
        "main/module/extra common scope, initialization or explicit SAVE masks the effect.\n"
        "The confirmation source inserts only one `save /saved_pair/` in each actual\n"
        "common-declaring procedure. Original8.5.5p3 supplies the confirmation permission;\n"
        "only `explicit-save-confirmation` is designated a positive-control facet.\n"
        "Its successful run is not counted as runtime-effect evidence.\n\n"
        "The defining SAVE/common/association rules and18.9.1p4 justify this Fortran-only\n"
        "retention witness without a C counterpart. No ABI, linker decoration, physical\n"
        "allocation or unsaved/undefined-value negative is observed. All eleven guard\n"
        "literals and the completion literal have bounded whole-program sensitivity plans;\n"
        "compile/link failures cannot qualify those runtime probes.\n\n"
        f"{len(requirement['pending'])} other {RULE} facets remain PENDING. Source and fixture\n"
        "review, current fingerprints, mode-qualified native observations and inventory\n"
        "renewal remain separate gates. The C819 material and all other requirements,\n"
        "canonical links and the current R402 SourceUse are not re-owned by this subset.\n\n")
    return before + begin + "\n\n" + section + end + after


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
    actual = {path for path in (ROOT / "tests/fixtures").glob("bind_common_save_*/*") if path.is_file()}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, raw in files.items()
                 if not path.is_file() or path.read_bytes() != raw]
        stale += [str(path.relative_to(ROOT)) for path in actual - set(files)]
        if catalogue != updated:
            stale.append(CATALOGUE)
        if (ROOT / VIEW).read_text() != view:
            stale.append(VIEW)
        if stale:
            raise SystemExit("stale BIND-common SAVE subset: " + ", ".join(sorted(stale)))
    else:
        if actual - set(files):
            raise ValueError("unexpected files in the bounded BIND-common SAVE corpus")
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if args.sync_catalogue:
            (ROOT / CATALOGUE).write_text(json.dumps(updated, indent=2) + "\n")
            (ROOT / VIEW).write_text(view)
    print(f"{'Checked' if args.check else 'Generated'} two BIND-common SAVE programs: one effect and one run control.")


if __name__ == "__main__":
    main()
