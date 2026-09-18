"""C851 dummy roles, exact repairs, calibrated causes and scoped regeneration."""
import copy
from dataclasses import asdict, replace
import hashlib
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from execution_commands import execution_context
from execution_validation import validate_case_trace
from suite_data import Registry, render_requirement, write_json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_optional_eligibility_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))
GNU_CAUSE = "Symbol at (1) is not a DUMMY variable"
FLANG_CAUSE = (
    "Only a dummy argument should have an INTENT, VALUE, or OPTIONAL attribute "
    "[-Wignore-irrelevant-attributes]"
)
SOURCES = {
    "data": (
        "subroutine optional_data_context()\n"
        "  implicit none\n"
        "  integer, optional :: subject\n"
        "end subroutine optional_data_context\n"
    ),
    "procedure": (
        "module optional_procedure_scope\n"
        "  implicit none\n"
        "  abstract interface\n"
        "    subroutine signature()\n"
        "    end subroutine signature\n"
        "  end interface\n"
        "contains\n"
        "  subroutine declaration_context()\n"
        "    implicit none\n"
        "    procedure(signature), optional :: callback\n"
        "  end subroutine declaration_context\n"
        "end module optional_procedure_scope\n"
    ),
}
CONTROL_HEADERS = {
    "data": "subroutine optional_data_context(subject)",
    "procedure": "  subroutine declaration_context(callback)",
}
UNSELECTED = "entry-and-attribute-source-boundaries"


class OptionalEligibilityFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}
        cls.transport_vectors = 0
        cls.generator_state_vectors = 0

    def case(self, variant, negative=False):
        return self.cases[generated.identifier(variant, negative)]

    def test_exact_owned_cases_facets_and_compile_only_roles(self):
        self.assertEqual(set(self.cases), {
            "C851_invalid__optional_data_nondummy",
            "C851_valid__optional_data_dummy_control",
            "C851_invalid__optional_procedure_nondummy",
            "C851_valid__optional_procedure_dummy_control",
        })
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {"data-dummy-admission", "procedure-dummy-admission", "nondummy-exclusion"})
        for case in self.cases.values():
            invalid = case.kind == "invalid"
            self.assertEqual((case.rule, case.meta.standard, case.meta.oracle_basis), ("C851", "f2023", "standard"))
            self.assertEqual(case.meta.evidence, "effect" if invalid else "positive-control")
            self.assertEqual(self.members[case.name]["cohort"], "diagnostic-only" if invalid else "positive-control")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertFalse(case.meta.reference_warnings)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step), ("compile", "source"))
            self.assertEqual(case.fixture.expectation.outcome, "diagnose" if invalid else "success")
            self.assertIsNone(case.fixture.link)
            if invalid:
                self.assertEqual(case.meta.facets, ["nondummy-exclusion"])
            else:
                admission = self.specs[case.name]["variant"] + "-dummy-admission"
                self.assertEqual(case.meta.facets, [admission, "nondummy-exclusion"])

    def test_complete_sources_and_header_only_insertion_repairs(self):
        for variant, expected in SOURCES.items():
            invalid = self.case(variant, True)
            control = self.case(variant)
            spec = self.specs[invalid.name]
            raw = (invalid.fixture.root / "source.f90").read_bytes()
            fixed = (control.fixture.root / "source.f90").read_bytes()
            self.assertEqual(raw, expected.encode("ascii"))
            expected_lines = expected.splitlines()
            expected_lines[spec["header_line"] - 1] = CONTROL_HEADERS[variant]
            self.assertEqual(fixed, ("\n".join(expected_lines) + "\n").encode("ascii"))
            repair = spec["repair"]
            offset, inserted = repair["insertion_byte_offset"], repair["inserted"].encode("ascii")
            self.assertEqual(fixed, raw[:offset] + inserted + raw[offset:])
            changed = [index + 1 for index, pair in enumerate(zip(raw.splitlines(), fixed.splitlines()))
                       if pair[0] != pair[1]]
            self.assertEqual(changed, [spec["header_line"]])
            self.assertEqual(len(raw.splitlines()), len(fixed.splitlines()))
            self.assertEqual((repair["negative_id"], repair["control_id"]), (invalid.name, control.name))
            self.assertEqual(repair["negative_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(repair["control_sha256"], hashlib.sha256(fixed).hexdigest())
            self.assertEqual(self.specs[control.name]["repair"], repair)
            for data in (raw, fixed):
                self.assertNotIn(b"\r", data)
                for token in (b"intent", b"pointer", b"save", b"value", b"=", b"call ",
                              b"allocate", b"associated", b"present(", b"print", b"bind(", b"[", b";"):
                    self.assertNotIn(token, data.lower())
                self.assertEqual(data.count(b"optional ::"), 1)
        self.assertEqual(self.specs[self.case("data", True).name]["declaration_line"], 3)
        self.assertEqual(self.specs[self.case("procedure", True).name]["declaration_line"], 10)

    def test_contracts_use_complete_measured_causes_and_only_declaration_origins(self):
        for variant, line in (("data", 3), ("procedure", 10)):
            diagnostic = self.case(variant, True).fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]),
                             ("source.f90", line, line))
            self.assertEqual(diagnostic["equals_any"], [GNU_CAUSE, FLANG_CAUSE])
            self.assertNotIn("contains_any", diagnostic)
            self.assertNotIn("additional_spans", diagnostic)
            self.assertEqual(diagnostic["allow_nonfatal"], [
                {"compiler": "flang", "severity": "warning", "equals_any": [FLANG_CAUSE]}])

    def staged(self, case, family, message=None, code=1, line=None, end_line=None, filename=None,
               severity=None, timed_out=False, echo_only=False, silent=False, tail="",
               codes=False, printed_code=False):
        """Mock transport only; parsing, private staging and judgement remain native."""
        compiler = runner.Compiler(family, family, dict(FAMILIES)[family], "synthetic transport, not calibration")
        fixture = case.fixture
        raw = (fixture.root / "source.f90").read_bytes()
        target = fixture.expectation.diagnostic["line"]
        first = target if line is None else line
        last = first if end_line is None else end_line
        cause = message if message is not None else (FLANG_CAUSE if family == "flang" else GNU_CAUSE)
        level = severity or ("warning" if family == "flang" else "error")
        calls = []

        def transport(command, cwd, timeout, stdin=None):
            source = Path(command[command.index("-c") + 1])
            workspace = Path(cwd).resolve()
            self.assertEqual((source.parent, source.name), (workspace, "source.f90"))
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual((command[0], timeout, stdin), (family, 5, None))
            lines = raw.decode("ascii").splitlines()
            source_line = lines[first - 1] if 1 <= first <= len(lines) else lines[target - 1]
            column = max(1, source_line.find(self.specs[case.name]["subject"]) + 1)
            location = str(source) if filename is None else filename
            reported = "syntax error" if echo_only else cause
            if family == "lfortran":
                tag = " [C851]" if printed_code else ""
                text = f"{location}:{first}-{last}:1-80: semantic {level}{tag}: {reported}\n"
            elif family == "gfortran":
                text = (f"{location}:{first}:{column}:\n\n {first:4} | {source_line}\n"
                        f"      | {' ' * (column - 1)}1\n{level.capitalize()}: {reported}\n")
            else:
                text = (f"{location}:{first}:{column}: {level}: {reported}\n"
                        f"  {source_line}\n  {' ' * (column - 1)}^^^^^^^^\n")
            if echo_only:
                text += f" {first:4} | ! {cause}\n      | 1\n"
            text = "" if silent else text + tail
            calls.append(dict(command=command, workspace=str(workspace)))
            return runner.ProcessResult(code, text, timed_out, "", text, b"", text.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(fixture, compiler, timeout=5, codes=codes)
        self.assertEqual((len(calls), check.phase, len(check.trace)), (1, "compile", 1))
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(raw).hexdigest()})
        self.assertEqual(check.execution_context, execution_context(calls[0]["workspace"], {}))
        self.assertFalse(validate_case_trace(
            self.members[case.name], asdict(check), dict(compiler.configuration(), version=compiler.version),
            ROOT, None, False))
        type(self).transport_vectors += 1
        return check

    def test_exact_causes_need_neither_fatal_status_nor_a_printed_rule_code(self):
        for variant, (family, _), status in itertools.product(SOURCES, FAMILIES, (0, 1, 2)):
            with self.subTest(variant=variant, family=family, status=status):
                check = self.staged(self.case(variant, True), family, code=status)
                self.assertEqual(check.outcome, "pass")
                self.assertEqual(check.note, "diagnoses without rejection" if status == 0 else "rejects")
        for variant in SOURCES:
            case = self.case(variant, True)
            self.assertEqual(self.staged(case, "lfortran", codes=True).outcome, "fail")
            self.assertEqual(self.staged(case, "lfortran", codes=True, printed_code=True).outcome, "pass")

    def test_wrapped_partial_wrong_condition_and_quoted_causes_fail(self):
        wrong = (
            "argument", "OPTIONAL", "DUMMY", "Symbol at (1)", "not a DUMMY variable",
            "OPTIONAL is not supported", "Procedure declarations are not yet implemented",
            "Only a dummy argument should have an INTENT attribute",
            "Missing interface", "Cannot read module optional_procedure_scope",
            "Unexpected end of file", "Expected END SUBROUTINE", "Syntax error in PROCEDURE statement",
        )
        prefixes = ("Internal: ", "Not yet implemented: ", "Unimplemented: ", "Unsupported: ",
                    "Internal error: ", "Verifier error: ", "Recovery: ")
        for variant, (family, _) in itertools.product(SOURCES, FAMILIES):
            case = self.case(variant, True)
            cause = FLANG_CAUSE if family == "flang" else GNU_CAUSE
            messages = wrong + tuple(prefix + cause for prefix in prefixes) + (
                'Example: "' + cause + '"', 'Unknown symbol "' + cause + '"',
                cause + " (unrelated example)", "Unrelated condition: " + cause,
            )
            for message in messages:
                with self.subTest(variant=variant, family=family, message=message):
                    self.assertEqual(self.staged(case, family, message).outcome, "fail")
            self.assertEqual(self.staged(case, family, echo_only=True).outcome, "fail")

    def test_only_live_staged_origins_and_exact_declaration_lines_qualify(self):
        for variant, (family, _) in itertools.product(SOURCES, FAMILIES):
            case = self.case(variant, True)
            target = case.fixture.expectation.diagnostic["line"]
            for origin in (None, "source.f90", "./source.f90"):
                self.assertEqual(self.staged(case, family, filename=origin).outcome, "pass")
            for origin in ("other.f90", "../source.f90", "unrelated/source.f90", "/foreign/source.f90"):
                self.assertEqual(self.staged(case, family, filename=origin).outcome, "fail")
            wrong_lines = {0, self.specs[case.name]["header_line"], target - 1, target + 1}
            if variant == "procedure":
                wrong_lines.add(4)
            for line in wrong_lines:
                self.assertEqual(self.staged(case, family, line=line).outcome, "fail")
            if family == "lfortran":
                for first, last in ((target - 1, target), (target, target + 1), (target + 1, target)):
                    self.assertEqual(self.staged(case, family, line=first, end_line=last).outcome, "fail")

    def test_only_the_measured_flang_warning_has_a_nonfatal_allowance(self):
        for variant, (family, _), severity, status in itertools.product(
                SOURCES, FAMILIES, ("warning", "portability"), (0, 1, 2)):
            with self.subTest(variant=variant, family=family, severity=severity, status=status):
                check = self.staged(self.case(variant, True), family, FLANG_CAUSE, code=status, severity=severity)
                self.assertEqual(check.outcome, "pass" if (family, severity) == ("flang", "warning") else "fail")
        for variant in SOURCES:
            for message in (GNU_CAUSE, FLANG_CAUSE + " extra", "Example: " + FLANG_CAUSE,
                            FLANG_CAUSE.removesuffix(" [-Wignore-irrelevant-attributes]")):
                self.assertEqual(self.staged(self.case(variant, True), "flang", message).outcome, "fail")

    def test_silence_native_internal_failures_and_abnormal_exits_do_not_count(self):
        for variant, (family, _) in itertools.product(SOURCES, FAMILIES):
            case = self.case(variant, True)
            for status in (0, 1, 2):
                self.assertEqual(self.staged(case, family, code=status, silent=True).outcome, "fail")
            for status in (-6, -11, 128, 134, 139):
                self.assertEqual(self.staged(case, family, code=status).outcome, "fail")
            self.assertEqual(self.staged(case, family, code=0, timed_out=True).outcome, "fail")
            for tail in ("\ninternal compiler error: failed\n", "\nASR verify pass error\n",
                         "\nout of memory\n", "\nLLVM ERROR: failed\n", "\nerror: Internal: failed\n"):
                self.assertEqual(self.staged(case, family, tail=tail).outcome, "fail")

    def test_controls_require_successful_object_production_without_link_or_run(self):
        scenarios = (
            (0, True, False, "", "pass"),
            (0, False, False, "", "fail"),
            (1, True, False, "error: rejected control\n", "fail"),
            (-11, True, False, "", "fail"),
            (0, True, True, "", "fail"),
            (0, True, False, "ASR verify pass error\n", "fail"),
        )
        for variant, (family, mode), scenario in itertools.product(SOURCES, FAMILIES, scenarios):
            status, object_exists, timed_out, output, outcome = scenario
            case = self.case(variant)
            compiler = runner.Compiler(family, family, mode, "synthetic positive transport")
            raw = (case.fixture.root / "source.f90").read_bytes()
            calls = []

            def transport(command, cwd, timeout, stdin=None):
                source = Path(command[command.index("-c") + 1])
                self.assertEqual((source.parent, source.name), (Path(cwd).resolve(), "source.f90"))
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual((timeout, stdin), (5, None))
                if object_exists:
                    Path(command[command.index("-o") + 1]).write_bytes(b"synthetic object, not compiler evidence")
                calls.append(command)
                return runner.ProcessResult(status, output, timed_out, "", output, b"", output.encode())

            with self.subTest(variant=variant, family=family, scenario=scenario), \
                    patch.object(runner, "run", side_effect=transport):
                check = runner.check_fixture(case.fixture, compiler, timeout=5)
            self.assertEqual((check.outcome, check.phase, len(calls)), (outcome, "compile", 1))
            self.assertFalse(validate_case_trace(
                self.members[case.name], asdict(check), dict(compiler.configuration(), version=compiler.version),
                ROOT, None, False))
            type(self).transport_vectors += 1

    def test_input_cause_origin_role_and_source_changes_invalidate_native_snapshot(self):
        for variant, mutation in itertools.product(SOURCES, ("source", "cause", "origin", "line", "span", "role")):
            original = self.case(variant, mutation != "role")
            fingerprint = original.fingerprint(self.registry)
            raw_manifest = original.fixture.path.read_bytes()
            raw_source = (original.fixture.root / "source.f90").read_bytes()
            with self.subTest(variant=variant, mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                path = directory / "fixture.json"
                path.write_bytes(raw_manifest)
                (directory / "source.f90").write_bytes(raw_source)

                def current_cases(*args, **kwargs):
                    fixture = runner.load_fixture(path, runner.PROFILES)
                    changed = replace(original, path=str(path), fixture=fixture, meta=fixture.meta)
                    return [changed if case.name == original.name else case for case in self.all_cases]

                cloned = next(case for case in current_cases() if case.name == original.name)
                self.assertEqual(cloned.fingerprint(self.registry), fingerprint)
                with patch.object(runner, "Registry", return_value=self.registry), \
                        patch.object(runner, "collect_cases", side_effect=current_cases):
                    self.assertEqual(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}), [])
                    manifest = json.loads(raw_manifest)
                    if mutation == "source":
                        (directory / "source.f90").write_bytes(raw_source + b"\n")
                    elif mutation == "role":
                        manifest["evidence"] = "effect"
                    else:
                        diagnostic = manifest["expect"]["diagnostic"]
                        if mutation == "cause":
                            diagnostic["equals_any"][0] += " changed"
                        elif mutation == "origin":
                            diagnostic["file"] = "other.f90"
                        elif mutation == "line":
                            diagnostic["line"] -= 1
                            diagnostic["end_line"] -= 1
                        else:
                            diagnostic["end_line"] += 1
                    path.write_text(json.dumps(manifest, indent=2) + "\n")
                    self.assertTrue(runner.confirm_snapshot([], [original], {original.review_key: fingerprint}))

    def test_source_requirement_changes_also_invalidate_selected_snapshots(self):
        registry = Registry(ROOT)
        case = self.case("data", True)
        fingerprint = case.fingerprint(registry)
        registry.requirements["C851"]["oracle_limitation"] += " Synthetic changed source contract."
        with patch.object(runner, "Registry", return_value=registry), \
                patch.object(runner, "collect_cases", return_value=self.all_cases):
            self.assertTrue(runner.confirm_snapshot([], [case], {case.review_key: fingerprint}))

    def test_generator_preserves_selected_unselected_control_and_review_state_matrix(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        for selected_mask, entry_state, foreign_state, review_state in itertools.product(
                range(8), ("original", "custom", "authored"), ("all", "partial", "none"),
                ("draft", "reviewed", "stale")):
            candidate = copy.deepcopy(catalogue)
            owner, foreign = candidate["requirements"]
            self.assertEqual((owner["id"], foreign["id"]), ("C851", "S8.5.12-001"))
            for bit, facet in enumerate(generated.FACETS):
                if selected_mask & (1 << bit):
                    owner["pending"][facet] = "Selected future text; only this owner's entry may be removed."
            if entry_state == "custom":
                owner["pending"][UNSELECTED] = "Foreign exact ENTRY plan with independently managed wording."
            elif entry_state == "authored":
                owner["pending"].pop(UNSELECTED, None)
            foreign["pending"] = {facet: "Foreign plan for " + facet for facet in foreign["facets"]}
            if foreign_state == "partial":
                foreign["pending"].pop(foreign["facets"][0])
            elif foreign_state == "none":
                foreign["pending"] = {}
            foreign["category"] = "effect"
            foreign["positive_control_facets"] = [foreign["facets"][0]]
            owner["oracle"] += "\n\nForeign oracle paragraph, retained verbatim."
            owner["oracle_limitation"] += "\n\nForeign limitation paragraph, retained verbatim."
            candidate["review_state"] = "draft" if review_state == "draft" else "reviewed"
            candidate["review_fingerprint"] = "0" * 64 if review_state == "stale" else "1" * 64
            candidate["review_rationale"] = "Synthetic raw lifecycle state; never a disk approval."
            untouched = copy.deepcopy(candidate)
            expected = copy.deepcopy(candidate)
            for facet in generated.FACETS:
                expected["requirements"][0]["pending"].pop(facet, None)
            actual = generated.synced_catalogue(candidate)
            self.assertEqual(actual, expected)
            self.assertEqual(candidate, untouched)
            self.assertEqual(generated.synced_catalogue(actual), actual)
            view = generated.render_view(actual)
            for row in actual["requirements"]:
                self.assertIn(render_requirement(row), view)
            self.assertNotIn("All implementation facets remain pending", view)
            self.assertNotIn("This registration adds no fixtures", view)
            self.assertNotIn("**Source review: reviewed.**", view)
            self.assertIn('Registry.catalogue_review_state("8.5.12")', view)
            type(self).generator_state_vectors += 1
        self.assertEqual(self.generator_state_vectors, 216)

    def test_effective_source_lifecycle_is_not_renewed_or_cached_by_generation(self):
        registry = Registry(ROOT)
        original = copy.deepcopy(registry.catalogues[generated.SECTION])
        for state in ("draft", "reviewed", "stale"):
            candidate = copy.deepcopy(original)
            registry.catalogues[generated.SECTION] = candidate
            candidate["review_state"] = "draft" if state == "draft" else "reviewed"
            candidate["review_rationale"] = "In-memory lifecycle, not a persisted review."
            candidate["review_fingerprint"] = ("0" * 64 if state == "stale"
                                               else registry.catalogue_fingerprint(generated.SECTION))
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)
            self.assertEqual(generated.synced_catalogue(candidate), candidate)
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)
            self.assertNotIn(f"**Source review: {state}.**", generated.render_view(candidate))
        self.assertEqual(Registry(ROOT).catalogues[generated.SECTION], original)

    def seed_generator_root(self, root, catalogue=None):
        for relative in (generated.CATALOGUE, generated.VIEW):
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        if catalogue is not None:
            write_json(root / generated.CATALOGUE, catalogue)

    def test_generator_is_idempotent_and_does_not_require_foreign_c851_family_ownership(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            catalogue = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            catalogue["requirements"][0]["pending"].pop(UNSELECTED, None)
            self.seed_generator_root(root, catalogue)
            generated.generate(root, sync_catalogue=True)
            foreign = root / "tests/fixtures/foreign_optional_owner"
            foreign.mkdir()
            manifest = copy.deepcopy(self.specs[self.case("data").name]["manifest"])
            manifest["id"] = "C851_valid__foreign_optional_boundary"
            manifest["facets"] = [UNSELECTED]
            write_json(foreign / "fixture.json", manifest)
            (foreign / "source.f90").write_bytes((self.case("data").fixture.root / "source.f90").read_bytes())
            source = dict(self.registry.standard, sections={generated.SECTION: self.registry.sections[generated.SECTION]})
            write_json(root / "source.json", source)
            (root / "rules.txt").write_text("C851 synthetic test inventory entry for the original constraint\n")
            write_json(root / "reviews.json", dict(schema_version=1, fixtures={}))
            write_json(root / "index.json", dict(
                schema_version=1, standard=self.registry.standard, source_inventory="source.json",
                rule_inventory="rules.txt", reviews="reviews.json", catalogues=[generated.CATALOGUE]))
            registry = Registry(root, "index.json")
            cases = runner.collect_cases(root / "tests", registry)
            self.assertEqual({case.name for case in cases}, set(self.cases) | {manifest["id"]})
            self.assertTrue(all(row["review"]["state"] == "unreviewed" for row in registry.execution._members(cases)))
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with patch.object(runner, "run", side_effect=AssertionError("generation must not invoke a compiler")):
                generated.generate(root, sync_catalogue=True)
                generated.generate(root, check=True)
                generated.generate(root, sync_catalogue=True)
                generated.generate(root, check=True)
                registry.render()
            after = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            self.assertEqual(after, before)
            self.assertEqual(len(cases), 5)

    def test_foreign_review_blockers_remain_in_full_native_inventory_and_snapshot(self):
        registry = Registry(ROOT)
        original_records = copy.deepcopy((registry.reviews, registry.evidence.data,
                                          registry.source_uses.data, registry.execution.data))
        before_snapshot = registry.execution.snapshot(self.all_cases)
        for case in self.cases.values():
            registry.reviews[case.review_key] = dict(
                state="source-reviewed", fingerprint=case.fingerprint(registry), sources=["C851"],
                rationale="In-memory owner-only lifecycle; not an approval on disk.")
        foreign = next(case for case in self.all_cases if case.name not in self.cases
                       and case.review_key in registry.reviews)
        registry.reviews[foreign.review_key] = dict(
            registry.reviews[foreign.review_key], state="unreviewed",
            rationale="Synthetic independent foreign blocker retained in the complete inventory.")
        members = registry.execution._members(self.all_cases)
        self.assertEqual({row["id"] for row in members}, {case.name for case in self.all_cases})
        self.assertEqual(next(row for row in members if row["id"] == foreign.name)["review"]["state"], "unreviewed")
        for report in registry.execution.report(self.all_cases, include_members=False):
            aggregate = registry.execution.aggregates[report["id"]]
            aggregate["review"] = dict(
                aggregate["review"], state="source-reviewed", fingerprint=report["review"]["fingerprint"],
                rationale="Synthetic matching raw inventory receipt cannot erase foreign blockers.")
        for report in registry.execution.report(self.all_cases, include_members=False):
            self.assertEqual(report["state"], "stale")
            self.assertEqual(report["member_count"], len(self.all_cases))
            self.assertIn(foreign.name + ": fixture review is unreviewed", report["blockers"])
        with patch.object(runner, "Registry", return_value=registry), \
                patch.object(runner, "collect_cases", return_value=self.all_cases):
            self.assertTrue(runner.confirm_snapshot([], [], {}, execution_snapshot=before_snapshot))
        fresh = Registry(ROOT)
        self.assertEqual((fresh.reviews, fresh.evidence.data, fresh.source_uses.data, fresh.execution.data),
                         original_records)

    def test_only_owned_oracle_paragraphs_are_replaced_and_duplicate_ownership_is_rejected(self):
        catalogue = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        owner = catalogue["requirements"][0]
        owner["oracle"] = "Foreign first.\n\n" + generated.ORACLE_PREFIX + "old owned text.\n\nForeign last."
        owner["oracle_limitation"] = "Foreign limitation."
        updated = generated.synced_catalogue(catalogue)["requirements"][0]
        self.assertEqual(updated["oracle"], "Foreign first.\n\n" + generated.ORACLE + "\n\nForeign last.")
        self.assertEqual(updated["oracle_limitation"], "Foreign limitation.\n\n" + generated.LIMITATION)
        owner["oracle"] += "\n\n" + generated.ORACLE_PREFIX + "duplicate."
        with self.assertRaisesRegex(ValueError, "duplicate owned"):
            generated.synced_catalogue(catalogue)

    def test_generated_files_are_byte_exact_and_check_mode_does_not_write(self):
        self.assertEqual(len(self.files), 8)
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
        self.assertEqual(generated.render_view(self.registry.catalogues[generated.SECTION]),
                         (ROOT / generated.VIEW).read_text())
        generated.generate(ROOT, check=True)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.seed_generator_root(root)
            generated.generate(root, sync_catalogue=True)
            changed = root / self.specs[self.case("data", True).name]["directory"] / "source.f90"
            changed.write_bytes(changed.read_bytes() + b"\n")
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with self.assertRaisesRegex(ValueError, "stale C851 eligibility family"):
                generated.generate(root, check=True)
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()},
                             before)


if __name__ == "__main__":
    unittest.main()
