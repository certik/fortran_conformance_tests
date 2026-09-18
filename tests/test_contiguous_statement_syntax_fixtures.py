"""R839 standalone forms, complete repairs, causal diagnostics and independent state."""
import copy
from dataclasses import asdict
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from execution_validation import validate_case_trace
from fixture_support import load_fixture
from suite_data import Registry, render_requirement, validate_case_requirement

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_contiguous_statement_syntax_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))


class ContiguousStatementSyntaxFixturesTests(unittest.TestCase):
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

    def case(self, form, invalid=False):
        return self.cases[generated.identifier(form, invalid)]

    def test_four_cases_cover_two_actual_statement_forms_and_both_missing_list_contrasts(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(set(self.cases), {
            generated.identifier(form, invalid) for form, invalid in itertools.product(generated.FORMS, (True, False))})
        self.assertEqual(len(self.files), 8)
        self.assertEqual(len({spec["source_sha256"] for spec in self.specs.values()}), 4)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets}, set(generated.FACETS))
        for form in generated.FORMS:
            self.assertEqual(self.case(form, True).meta.facets, ["missing-object-list"])
            self.assertEqual(self.case(form).meta.facets, [generated.FORMS[form], "missing-object-list"])
        for case in self.cases.values():
            invalid = case.kind == "invalid"
            self.assertEqual((case.rule, case.meta.standard, case.meta.oracle_basis), ("R839", "f2023", "standard"))
            self.assertEqual(case.meta.evidence, "effect" if invalid else "positive-control")
            self.assertEqual(self.members[case.name]["cohort"], "diagnostic-only" if invalid else "positive-control")
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertIsNone(case.fixture.link)
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step), ("compile", "source"))
            self.assertEqual(case.fixture.expectation.outcome, "diagnose" if invalid else "success")

    def test_each_repair_inserts_only_separated_subject_and_keeps_its_standalone_form(self):
        for form in generated.FORMS:
            bad = (self.case(form, True).fixture.root / "source.f90").read_bytes()
            good = (self.case(form).fixture.root / "source.f90").read_bytes()
            repair = self.specs[self.case(form, True).name]["repair"]
            start, end = repair["span"]
            self.assertEqual(start, end)
            self.assertEqual((repair["removed"], repair["replacement"]), ("", " subject"))
            self.assertEqual(bad[:start] + b" subject" + bad[end:], good)
            self.assertEqual(bad[:start].count(b"\n") + 1, 4)
            self.assertEqual(repair["control_id"], self.case(form).name)
            self.assertEqual(repair["control_sha256"], generated.sha(good))
            self.assertEqual([n + 1 for n, (a, b) in enumerate(zip(bad.splitlines(), good.splitlines())) if a != b], [4])
            self.assertEqual(len(bad.splitlines()), len(good.splitlines()))
            self.assertEqual(bad.splitlines()[3], b"  contiguous" + (b" ::" if form == "double_colon" else b""))
            self.assertEqual(good.splitlines()[3], bad.splitlines()[3] + b" subject")

    def test_complete_ordinary_array_pointer_context_has_no_association_or_runtime_oracle(self):
        for spec in self.specs.values():
            source = spec["source"]
            lines = source.splitlines()
            self.assertEqual(len(lines), 5)
            self.assertEqual(lines[:3], [
                "module contiguous_statement_syntax_scope",
                "  implicit none",
                "  integer, pointer :: subject(:)"])
            self.assertEqual(lines[-1], "end module contiguous_statement_syntax_scope")
            self.assertNotIn("contiguous", lines[2])
            self.assertNotIn("=", source)
            self.assertNotIn("[", source)
            self.assertNotRegex(source, r"(?i)\b(allocatable|target|save|parameter|associated|is_contiguous|"
                                       r"allocate|call|print|subroutine|function|bind|common)\b")
            self.assertNotIn("\r", source)
            source.encode("ascii")
            self.assertLessEqual(max(map(len, lines)), 132)

    def test_exact_missing_names_cause_has_only_the_live_statement_and_no_extra_allowance(self):
        for form in generated.FORMS:
            diagnostic = self.case(form, True).fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]), ("source.f90", 4, 4))
            expected = ["expected object names", "Invalid character in name at (1)"]
            if form == "double_colon":
                expected.append("Newline is unexpected here")
            self.assertEqual(diagnostic["equals_any"], expected)
            for cause in expected:
                self.assertFalse(any(exclusion.lower() in cause.lower() for exclusion in diagnostic["excludes_any"]))
            for field in ("contains_any", "allow_nonfatal", "additional_spans"):
                self.assertNotIn(field, diagnostic)

    def staged(self, case, family, *, cause=generated.CAUSE, status=1, line=4, end_line=None,
               filename=None, severity="error", silent=False, echo=False, tail="",
               timeout=False, codes=False, printed_code=False, context_only=False, malformed_origin=False):
        compiler = runner.Compiler(family, family, dict(FAMILIES)[family], "synthetic transport, not calibration")
        raw = (case.fixture.root / "source.f90").read_bytes()
        calls = []

        def transport(command, cwd, wait, stdin=None):
            source = Path(command[command.index("-c") + 1])
            self.assertEqual((source.parent, source.name), (Path(cwd).resolve(), "source.f90"))
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual((command[0], wait, stdin), (family, 5, None))
            location = str(source) if filename is None else filename
            text = "Unrelated syntax error" if echo else cause
            shown = raw.decode().splitlines()[3]
            if family == "lfortran":
                tag = " [R839]" if printed_code else ""
                output = f"{location}:{line}-{line if end_line is None else end_line}:3-16: syntax {severity}{tag}: {text}\n"
            elif family == "gfortran":
                output = (f"{location}:{line}:{len(shown)}:\n\n {line:4} | {shown}\n"
                          f"      | {' ' * len(shown)}1\n{severity.capitalize()}: {text}\n")
            else:
                output = f"{location}:{line}:{len(shown) + 1}: {severity}: {text}\n  {shown}\n    ^\n"
            if context_only:
                output = (f"{location}:{line}:3: in the context: specification construct\n"
                          f"{severity.capitalize()}: {text}\n")
            if malformed_origin:
                output = output.replace(f"{location}:{line}", f"{location}:not-a-line", 1)
            if echo:
                output += f"    4 | ! {cause}\n      | 1\n"
            output = "" if silent else output + tail
            calls.append(list(command))
            return runner.ProcessResult(status, output, timeout, "", output, b"", output.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5, codes=codes)
        self.assertEqual((len(calls), len(check.trace), check.phase), (1, 1, "compile"))
        self.assertEqual(check.input_hashes, {"source.f90": generated.sha(raw)})
        self.assertFalse(validate_case_trace(self.members[case.name], asdict(check),
                                            dict(compiler.configuration(), version=compiler.version), ROOT, None, False))
        type(self).transport_vectors += 1
        return check

    def test_precise_cause_does_not_require_rejection_or_a_printed_rule(self):
        for form in generated.FORMS:
            for (family, _), cause, status in itertools.product(FAMILIES, generated.CAUSES[form], (0, 1, 2)):
                self.assertEqual(self.staged(self.case(form, True), family, cause=cause, status=status).outcome, "pass")
            for cause in generated.CAUSES[form]:
                self.assertEqual(self.staged(self.case(form, True), "lfortran", cause=cause, codes=True).outcome, "fail")
                self.assertEqual(self.staged(self.case(form, True), "lfortran", cause=cause,
                                             codes=True, printed_code=True).outcome, "pass")

    def test_newline_cause_is_bound_to_the_double_colon_case_not_the_bare_form(self):
        for family, _ in FAMILIES:
            self.assertEqual(self.staged(self.case("double_colon", True), family,
                                         cause="Newline is unexpected here").outcome, "pass")
            self.assertEqual(self.staged(self.case("no_colon", True), family,
                                         cause="Newline is unexpected here").outcome, "fail")
            for form in generated.FORMS:
                self.assertEqual(self.staged(self.case(form, True), family,
                                             cause="Attribute declaration not supported yet").outcome, "fail")

    def test_unlisted_partial_wrapped_quoted_and_echoed_causes_are_not_promoted(self):
        wrong = (
            "CONTIGUOUS", "object", "object names", "expected name", "syntax error",
            "Invalid character in name", "Invalid character in name at (2)",
            "Attribute declaration not supported yet", "Newline", "Newline is unexpected",
            "unexpected EOF", "Missing END MODULE",
            "CONTIGUOUS requires an array pointer", "Symbol subject has no implicit type",
        )
        for form, (family, _) in itertools.product(generated.FORMS, FAMILIES):
            case = self.case(form, True)
            for cause in wrong:
                self.assertEqual(self.staged(case, family, cause=cause).outcome, "fail")
            for cause in generated.CAUSES[form]:
                wrong_wrappers = (
                    "Unrelated condition: " + cause, cause + " (example)",
                    'Example: "' + cause + '"', 'Unknown symbol "' + cause + '"',
                ) + tuple(prefix + cause for prefix in ("Unsupported: ", "Not implemented: ", "Internal: ", "Recovery: "))
                for message in wrong_wrappers:
                    self.assertEqual(self.staged(case, family, cause=message).outcome, "fail")
                self.assertEqual(self.staged(case, family, cause=cause, echo=True).outcome, "fail")

    def test_only_physical_statement_origin_qualifies_not_END_or_widened_lookahead(self):
        for form in generated.FORMS:
            for (family, _), cause in itertools.product(FAMILIES, generated.CAUSES[form]):
                case = self.case(form, True)
                for filename in (None, "source.f90", "./source.f90"):
                    self.assertEqual(self.staged(case, family, cause=cause, filename=filename).outcome, "pass")
                for filename in ("foreign.f90", "/unrelated/source.f90", "missing/source.f90"):
                    self.assertEqual(self.staged(case, family, cause=cause, filename=filename).outcome, "fail")
                for line in (1, 3, 5, 6):
                    self.assertEqual(self.staged(case, family, cause=cause, line=line).outcome, "fail")
                if family == "lfortran":
                    self.assertEqual(self.staged(case, family, cause=cause, line=3, end_line=4).outcome, "fail")
                    self.assertEqual(self.staged(case, family, cause=cause, end_line=5).outcome, "fail")
                self.assertEqual(self.staged(case, family, cause=cause, context_only=True).outcome, "fail")
                self.assertEqual(self.staged(case, family, cause=cause, malformed_origin=True).outcome, "fail")
                for status in (0, 1):
                    self.assertEqual(self.staged(case, family, cause=cause, status=status, silent=True).outcome, "fail")
                    self.assertEqual(self.staged(case, family, cause=cause, status=status, severity="warning").outcome, "fail")
                self.assertEqual(self.staged(case, family, cause=cause, timeout=True).outcome, "fail")
                for status in (-11, 139):
                    self.assertEqual(self.staged(case, family, cause=cause, status=status).outcome, "fail")
                for tail in ("\nASR verify pass error\n",
                             "\n/unrelated/foreign.f90:1:1: error: Internal: compiler failure\n",
                             "\nf951: Fatal Error: out of memory\n"):
                    self.assertEqual(self.staged(case, family, cause=cause, tail=tail).outcome, "fail")

    def test_controls_compile_once_require_real_objects_and_have_no_runtime_phase(self):
        for form, (family, mode), fault in itertools.product(
                generated.FORMS, FAMILIES, (None, "missing-object", "error", "internal", "timeout")):
            case = self.case(form)
            compiler = runner.Compiler(family, family, mode, "synthetic transport")
            calls = []

            def transport(command, cwd, timeout, stdin=None):
                calls.append(list(command))
                self.assertIn("-c", command)
                self.assertEqual(Path(command[command.index("-c") + 1]).read_bytes(),
                                 (case.fixture.root / "source.f90").read_bytes())
                if fault is None:
                    Path(command[command.index("-o") + 1]).write_bytes(b"synthetic object")
                output = "ASR verify pass error\n" if fault == "internal" else ""
                return runner.ProcessResult(1 if fault == "error" else 0, output, fault == "timeout",
                                            "", output, b"", output.encode())

            with patch.object(runner, "run", side_effect=transport):
                check = runner.check_fixture(case.fixture, compiler, timeout=5)
            self.assertEqual(check.outcome, "pass" if fault is None else "fail")
            self.assertEqual((len(calls), len(check.trace), check.phase), (1, 1, "compile"))
            type(self).transport_vectors += 1

    def test_unselected_facet_plans_and_raw_source_reviews_survive_all_independent_states(self):
        original = self.registry.catalogues[generated.SECTION]
        others = sorted(set(self.registry.requirements[generated.RULE]["facets"]) - set(generated.FACETS))
        for owned_mask, foreign_mask, state in itertools.product(
                range(1 << len(generated.FACETS)), range(1 << len(others)), ("draft", "reviewed", "stale")):
            candidate = copy.deepcopy(original)
            owner = next(row for row in candidate["requirements"] if row["id"] == generated.RULE)
            for bit, facet in enumerate(generated.FACETS):
                if owned_mask & (1 << bit):
                    owner["pending"][facet] = "Selected revised plan."
            for bit, facet in enumerate(others):
                if foreign_mask & (1 << bit):
                    owner["pending"][facet] = "Foreign exact plan: " + facet
                else:
                    owner["pending"].pop(facet, None)
            owner["oracle"] += "\n\nForeign oracle."
            owner["oracle_limitation"] += "\n\nForeign limitation."
            candidate.update(review_state="draft" if state == "draft" else "reviewed",
                             review_fingerprint=("0" if state == "stale" else "1") * 64,
                             review_rationale="Synthetic preservation state, not an approval.")
            before, expected = copy.deepcopy(candidate), copy.deepcopy(candidate)
            for facet in generated.FACETS:
                next(row for row in expected["requirements"] if row["id"] == generated.RULE)["pending"].pop(facet, None)
            actual = generated.synced_catalogue(candidate)
            self.assertEqual(candidate, before)
            self.assertEqual(actual, expected)
            self.assertEqual(generated.synced_catalogue(actual), actual)
            self.assertTrue(all(render_requirement(row) in generated.render_view(actual) for row in actual["requirements"]))
            type(self).generator_state_vectors += 1

    def test_foreign_actual_requirement_record_is_preserved_not_rewritten(self):
        candidate = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        foreign = copy.deepcopy(self.registry.requirements["C830"])
        candidate["requirements"].append(foreign)
        before = copy.deepcopy(candidate)
        actual = generated.synced_catalogue(candidate)
        self.assertEqual(candidate, before)
        self.assertEqual(actual["requirements"][-1], foreign)
        self.assertIn(render_requirement(foreign), generated.render_view(actual))

    def test_rendering_is_lifecycle_neutral_after_current_or_stale_source_reviews(self):
        summaries = []
        for state in ("draft", "reviewed", "stale"):
            registry = Registry(ROOT)
            catalogue = registry.catalogues[generated.SECTION]
            catalogue["review_state"] = "draft" if state == "draft" else "reviewed"
            catalogue["review_fingerprint"] = (
                "0" * 64 if state == "stale" else registry.catalogue_fingerprint(generated.SECTION))
            catalogue["review_rationale"] = "Synthetic renderer state, not an approval."
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), state)
            before = copy.deepcopy(catalogue)
            synced = generated.synced_catalogue(catalogue)
            self.assertEqual(synced, before)
            text = generated.render_view(synced)
            summary = text.split(generated.SUMMARY_BEGIN)[1].split(generated.SUMMARY_END)[0]
            summaries.append(summary)
            prose = summary + generated.ORACLE + generated.LIMITATION
            for stale_assertion in (
                    "The packet is unapproved", "Actual Flang reports it in f2018",
                    "GNU's generic name error", "no f2023 reference-qualified negative",
                    "No f2023 reference-qualified negative", "both one-insertion repairs compile",
                    "the three recorded configurations", "remain nonqualifying failures"):
                self.assertNotIn(stale_assertion, prose)
            self.assertIn("alone grants no approval", summary)
            self.assertIn("effective source/case reviews", summary)
            self.assertIn("immutable", summary)
            self.assertEqual(catalogue, before)
        self.assertEqual(summaries, [summaries[0]] * 3)

    def test_selected_definitions_and_unique_owned_paragraphs_are_required(self):
        for facet in generated.FACETS:
            candidate = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            next(row for row in candidate["requirements"] if row["id"] == generated.RULE)["facets"].remove(facet)
            before = copy.deepcopy(candidate)
            with self.assertRaisesRegex(ValueError, "selected R839 source/facet"):
                generated.synced_catalogue(candidate)
            self.assertEqual(candidate, before)
        for field, value in (("category", "effect"), ("diagnostic_obligation", "not-required")):
            candidate = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            next(row for row in candidate["requirements"] if row["id"] == generated.RULE)[field] = value
            with self.assertRaisesRegex(ValueError, "selected R839 source/facet"):
                generated.synced_catalogue(candidate)
        candidate = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        candidate["requirements"][0]["oracle"] += "\n\n" + generated.ORACLE_PREFIX + "duplicate"
        with self.assertRaisesRegex(ValueError, "duplicate owned"):
            generated.synced_catalogue(candidate)

    def test_legacy_all_pending_banner_is_removed_without_touching_foreign_prose(self):
        candidate = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        owner = next(row for row in candidate["requirements"] if row["id"] == generated.RULE)
        owner["oracle_limitation"] = "All facets are pending. Foreign original limitation."
        actual = generated.synced_catalogue(candidate)["requirements"][0]["oracle_limitation"]
        self.assertTrue(actual.startswith("Foreign original limitation.\n\n" + generated.LIMIT_PREFIX))
        self.assertEqual(owner["oracle_limitation"], "All facets are pending. Foreign original limitation.")

    def test_standalone_generation_preserves_foreign_bytes_and_validates_only_owned_rules(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (generated.CATALOGUE, generated.VIEW):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            view = root / generated.VIEW
            view.write_text("Foreign exact preface.\n\n" + view.read_text())
            generated.generate(root, sync_catalogue=True)
            foreign = root / "tests/fixtures/contiguous_statement_syntax_foreign"
            foreign.mkdir()
            (foreign / "source.f90").write_text("Foreign bytes.\n")
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with patch.object(runner, "run", side_effect=AssertionError("generation must not invoke compilers")):
                for _ in range(2):
                    generated.generate(root, sync_catalogue=True)
                    generated.generate(root, check=True)
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)
            requirement = json.loads((root / generated.CATALOGUE).read_text())["requirements"][0]
            for path in generated.build_corpus(root)[0]:
                if path.name != "fixture.json":
                    continue
                fixture = load_fixture(path, runner.PROFILES)
                case = runner.SuiteCase(fixture.name, fixture.rule, fixture.kind, str(path),
                                        fixture.meta, fixture.name, fixture=fixture)
                validate_case_requirement(case, requirement, numbered=True)

    def test_changed_owner_stales_all_actual_R839_cases_without_freezing_a_foreign_census(self):
        registry = Registry(ROOT)
        before = {case.name: case.fingerprint(registry) for case in self.all_cases}
        registry.requirements[generated.RULE]["oracle_limitation"] += " Changed current owner gate."
        changed = {case.name for case in self.all_cases if case.fingerprint(registry) != before[case.name]}
        self.assertEqual(changed, {case.name for case in self.all_cases if case.rule == generated.RULE})
        self.assertTrue(set(self.cases) <= changed)
        self.assertEqual(len({case.review_key for case in self.cases.values()}), 4)

    def test_generated_inputs_and_check_only_native_render_are_exact(self):
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)
        self.registry.render(write=False)
        self.assertEqual(generated.build_corpus()[0], self.files)


if __name__ == "__main__":
    unittest.main()
