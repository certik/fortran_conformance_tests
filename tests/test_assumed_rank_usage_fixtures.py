"""Exact C839/C840 repairs, real diagnostic transport and independent ownership."""
import copy
from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from execution_validation import validate_case_trace
from suite_data import Registry, render_requirement

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_assumed_rank_effect_fixtures as rank_effects
import generate_assumed_rank_usage_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))


class AssumedRankUsageFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        paths = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in paths}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}
        cls.transport_vectors = 0
        cls.generator_state_vectors = 0

    def case(self, variant, invalid=False):
        return self.cases[generated.identifier(variant, invalid)]

    def test_four_owned_compile_cases_only_close_two_exclusion_facets(self):
        self.assertEqual(set(self.cases), {
            "C839_invalid__assumed_rank_local", "C839_valid__assumed_rank_local_control",
            "C840_invalid__assumed_rank_expression", "C840_valid__assumed_rank_expression_control",
        })
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 8)
        for case in self.cases.values():
            spec = self.specs[case.name]
            invalid = case.kind == "invalid"
            self.assertEqual((case.rule, case.meta.facets), (spec["rule"], spec["facets"]))
            self.assertEqual(case.meta.evidence, "effect" if invalid else "positive-control")
            self.assertEqual(self.members[case.name]["cohort"], "diagnostic-only" if invalid else "positive-control")
            self.assertEqual((case.meta.standard, case.meta.oracle_basis), ("f2023", "standard"))
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertFalse(case.meta.reference_warnings)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertIsNone(case.fixture.link)
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step), ("compile", "source"))
            self.assertEqual(case.fixture.expectation.outcome, "diagnose" if invalid else "success")
        claimed = {facet for case in self.cases.values() for facet in case.meta.facets}
        self.assertNotIn("dummy-admission", claimed)
        self.assertNotIn("first-inquiry-dummy", claimed)

    def test_repairs_change_exactly_one_site_and_preserve_complete_source(self):
        for variant in generated.SCOPES:
            invalid, control = self.case(variant, True), self.case(variant)
            spec = self.specs[invalid.name]
            raw = (invalid.fixture.root / "source.f90").read_bytes()
            fixed = (control.fixture.root / "source.f90").read_bytes()
            repair = spec["repair"]
            start, end = repair["span"]
            self.assertEqual(raw[start:end].decode(), repair["old"])
            self.assertEqual(fixed, raw[:start] + repair["replacement"].encode() + raw[end:])
            self.assertEqual([index + 1 for index, pair in enumerate(zip(raw.splitlines(), fixed.splitlines()))
                              if pair[0] != pair[1]], [repair["line"]])
            self.assertEqual(len(raw.splitlines()), len(fixed.splitlines()))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), repair["negative_sha256"])
            self.assertEqual(hashlib.sha256(fixed).hexdigest(), repair["control_sha256"])
            self.assertEqual(self.specs[control.name]["repair"], repair)
            self.assertNotIn(b"\r", raw)
            self.assertNotIn(b";", raw)
            self.assertLessEqual(max(map(len, raw.splitlines())), 132)
        local = self.specs[self.case("local", True).name]["source"]
        self.assertEqual(local,
                         "subroutine assumed_rank_local_context()\n"
                         "  implicit none\n"
                         "  integer :: subject(..)\n"
                         "end subroutine assumed_rank_local_context\n")
        control = self.specs[self.case("local").name]["source"]
        self.assertEqual(control.replace("context(subject)", "context()"), local)
        self.assertNotRegex(local, r"\b(call|print|intent|optional|pointer|value|allocatable|save)\b")

    def test_expression_pair_has_a_defined_scalar_and_real_explicit_interface(self):
        for invalid in (True, False):
            source = self.specs[self.case("expression", invalid).name]["source"]
            lines = source.splitlines()
            self.assertEqual(lines[3:5], ["  subject=7", "  call observe(subject)"])
            self.assertEqual(lines[5:9], [
                "contains", "  subroutine observe(x)", "    implicit none", "    integer, intent(in) :: x(..)"])
            self.assertEqual(lines[9], "    print *, x" if invalid else "    print *, rank(x)")
            self.assertEqual(lines[-2:], ["  end subroutine observe", "end program assumed_rank_expression_context"])
            self.assertEqual(source.count("rank(x)"), 0 if invalid else 1)
            self.assertNotRegex(source, r"\b(optional|pointer|allocatable|value|contiguous|bind|class|type)\b")
            self.assertNotIn("select rank", source)
            self.assertNotIn("rank([", source)

    def test_exact_diagnostic_routes_are_finite_and_have_no_nonfatal_or_widened_origin(self):
        for variant, (_, _, line) in generated.SCOPES.items():
            diagnostic = self.case(variant, True).fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]), ("source.f90", line, line))
            self.assertEqual(diagnostic["equals_any"], list(generated.CAUSES[variant]))
            for field in ("contains_any", "allow_nonfatal", "additional_spans"):
                self.assertNotIn(field, diagnostic)
        self.assertIn("Assumed-rank arrays are not supported in print statements",
                      self.case("expression", True).fixture.expectation.diagnostic["equals_any"])

    def staged(self, case, family, *, cause=None, status=1, line=None, end_line=None, filename=None,
               severity="error", tail="", echo=False, silent=False, timeout=False, codes=False,
               printed_code=False):
        compiler = runner.Compiler(family, family, dict(FAMILIES)[family], "synthetic transport, not calibration")
        spec = self.specs[case.name]
        target = spec["diagnostic_line"]
        first = target if line is None else line
        last = first if end_line is None else end_line
        if cause is None:
            index = {"lfortran": 0, "gfortran": 1, "flang": 2 if spec["variant"] == "local" else 1}[family]
            cause = generated.CAUSES[spec["variant"]][index]
        raw = (case.fixture.root / "source.f90").read_bytes()
        calls = []

        def transport(command, cwd, wait, stdin=None):
            workspace = Path(cwd).resolve()
            source = Path(command[command.index("-c") + 1])
            self.assertEqual((source.parent, source.name), (workspace, "source.f90"))
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual((command[0], wait, stdin), (family, 5, None))
            location = str(source) if filename is None else filename
            shown = raw.decode().splitlines()[target - 1]
            actual = "syntax error" if echo else cause
            if family == "lfortran":
                code = " [" + case.rule + "]" if printed_code else ""
                text = f"{location}:{first}-{last}:1-80: semantic {severity}{code}: {actual}\n"
            elif family == "gfortran":
                text = (f"{location}:{first}:14:\n\n {first:4} | {shown}\n"
                        f"      |              1\n{severity.capitalize()}: {actual}\n")
            else:
                text = f"{location}:{first}:14: {severity}: {actual}\n  {shown}\n               ^\n"
            if echo:
                text += f" {target:4} | ! {cause}\n      | 1\n"
            text = "" if silent else text + tail
            calls.append(list(command))
            return runner.ProcessResult(status, text, timeout, "", text, b"", text.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, compiler, timeout=5, codes=codes)
        self.assertEqual((len(calls), len(check.trace), check.phase), (1, 1, "compile"))
        self.assertEqual(check.input_hashes, {"source.f90": hashlib.sha256(raw).hexdigest()})
        self.assertFalse(validate_case_trace(self.members[case.name], asdict(check),
                                            dict(compiler.configuration(), version=compiler.version),
                                            ROOT, None, False))
        type(self).transport_vectors += 1
        return check

    def test_exact_causes_are_required_but_fatal_status_and_printed_codes_are_not(self):
        for variant, (family, _), status in itertools.product(generated.SCOPES, FAMILIES, (0, 1, 2)):
            self.assertEqual(self.staged(self.case(variant, True), family, status=status).outcome, "pass")
        for variant in generated.SCOPES:
            case = self.case(variant, True)
            self.assertEqual(self.staged(case, "lfortran", codes=True).outcome, "fail")
            self.assertEqual(self.staged(case, "lfortran", codes=True, printed_code=True).outcome, "pass")

    def test_generic_unavailable_feature_wrapped_quoted_or_wrong_subject_messages_do_not_qualify(self):
        generic = (
            "Assumed-rank arrays are not supported",
            "Assumed-rank array printing is not yet implemented",
            "PRINT statements are not supported",
            "Assumed-rank variable x is not supported",
            "Unexpected rank in PRINT",
            "Must be a dummy argument",
            "Assumed-rank array 'different' must be a dummy argument",
            "Assumed-rank variable different at (1) may only be used as actual argument",
        )
        for variant, (family, _) in itertools.product(generated.SCOPES, FAMILIES):
            case = self.case(variant, True)
            for cause in generated.CAUSES[variant]:
                wrong = generic + tuple(prefix + cause for prefix in
                                        ("Unsupported: ", "Not implemented: ", "Internal: ", "Recovery: ")) + (
                    'Example: "' + cause + '"', 'Unknown symbol "' + cause + '"',
                    cause + " (example)", "Unrelated condition: " + cause)
                for message in wrong:
                    self.assertEqual(self.staged(case, family, cause=message).outcome, "fail")
                self.assertEqual(self.staged(case, family, cause=cause, echo=True).outcome, "fail")

    def test_live_staged_declaration_or_expression_is_the_only_allowed_origin(self):
        for variant, (family, _) in itertools.product(generated.SCOPES, FAMILIES):
            case = self.case(variant, True)
            target = generated.SCOPES[variant][2]
            for filename in (None, "source.f90", "./source.f90"):
                self.assertEqual(self.staged(case, family, filename=filename).outcome, "pass")
            for filename in ("foreign.f90", "/unrelated/source.f90", "missing/source.f90"):
                self.assertEqual(self.staged(case, family, filename=filename).outcome, "fail")
            for line in (1, target - 1, target + 1):
                self.assertEqual(self.staged(case, family, line=line).outcome, "fail")
            if family == "lfortran":
                self.assertEqual(self.staged(case, family, line=target - 1, end_line=target).outcome, "fail")
                self.assertEqual(self.staged(case, family, line=target, end_line=target + 1).outcome, "fail")

    def test_silence_warnings_crashes_and_global_compiler_failures_are_never_reporting_credit(self):
        for variant, (family, _) in itertools.product(generated.SCOPES, FAMILIES):
            case = self.case(variant, True)
            for status in (0, 1):
                self.assertEqual(self.staged(case, family, status=status, silent=True).outcome, "fail")
                self.assertEqual(self.staged(case, family, status=status, severity="warning").outcome, "fail")
            self.assertEqual(self.staged(case, family, timeout=True).outcome, "fail")
            self.assertEqual(self.staged(case, family, status=-11).outcome, "fail")
            self.assertEqual(self.staged(case, family, status=139).outcome, "fail")
            for text in ("ASR verify pass error", "Internal: compiler failure"):
                tail = "\n/unrelated/foreign.f90:1:1: error: " + text + "\n"
                with self.subTest(variant=variant, family=family, failure=text):
                    self.assertEqual(self.staged(case, family, tail=tail).outcome, "fail")
            self.assertEqual(self.staged(case, family, tail="\nf951: Fatal Error: out of memory\n").outcome, "fail")

    def test_controls_require_objects_and_never_link_or_run(self):
        for variant, (family, _), fault in itertools.product(
                generated.SCOPES, FAMILIES, (None, "missing-object", "error", "internal", "timeout")):
            case = self.case(variant)
            compiler = runner.Compiler(family, family, dict(FAMILIES)[family], "synthetic transport")
            calls = []

            def transport(command, cwd, timeout, stdin=None):
                calls.append(list(command))
                self.assertIn("-c", command)
                self.assertEqual(Path(command[command.index("-c") + 1]).read_bytes(),
                                 (case.fixture.root / "source.f90").read_bytes())
                if fault is None:
                    Path(command[command.index("-o") + 1]).write_bytes(b"synthetic object")
                text = "ASR verify pass error\n" if fault == "internal" else ""
                return runner.ProcessResult(1 if fault == "error" else 0, text, fault == "timeout",
                                            "", text, b"", text.encode())

            with patch.object(runner, "run", side_effect=transport):
                result = runner.check_fixture(case.fixture, compiler, timeout=5)
            self.assertEqual(result.outcome, "pass" if fault is None else "fail")
            self.assertEqual((len(calls), len(result.trace), result.phase), (1, 1, "compile"))
            type(self).transport_vectors += 1

    def test_each_unselected_owner_subset_and_all_foreign_lifecycle_fields_are_preserved(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        selected = {rule: facet for rule, facet, _ in generated.SCOPES.values()}
        for rule, facet in selected.items():
            unselected = [f for f in self.registry.requirements[rule]["facets"] if f != facet]
            for mask, pending_selected, state in itertools.product(range(1 << len(unselected)),
                                                                   (True, False), ("draft", "reviewed", "stale")):
                candidate = copy.deepcopy(catalogue)
                owner = next(row for row in candidate["requirements"] if row["id"] == rule)
                owner["pending"] = {name: "Foreign plan: " + name for bit, name in enumerate(unselected)
                                    if mask & (1 << bit)}
                if pending_selected:
                    owner["pending"][facet] = "Owned plan."
                owner["positive_control_facets"] = [unselected[0]]
                owner["oracle"] += "\n\nForeign oracle paragraph."
                owner["oracle_limitation"] += "\n\nForeign limitation paragraph."
                candidate.update(review_state="draft" if state == "draft" else "reviewed",
                                 review_fingerprint=("0" if state == "stale" else "1") * 64,
                                 review_rationale="Synthetic foreign raw state, never approval.")
                before = copy.deepcopy(candidate)
                expected = copy.deepcopy(candidate)
                next(row for row in expected["requirements"] if row["id"] == rule)["pending"].pop(facet, None)
                actual = generated.synced_catalogue(candidate)
                self.assertEqual(actual, expected)
                self.assertEqual(candidate, before)
                self.assertEqual(generated.synced_catalogue(actual), actual)
                type(self).generator_state_vectors += 1

    def test_selected_definitions_and_unique_owned_paragraphs_are_required(self):
        for rule, facet, _ in generated.SCOPES.values():
            catalogue = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            owner = next(row for row in catalogue["requirements"] if row["id"] == rule)
            owner["facets"].remove(facet)
            before = copy.deepcopy(catalogue)
            with self.assertRaisesRegex(ValueError, "selected assumed-rank usage"):
                generated.synced_catalogue(catalogue)
            self.assertEqual(catalogue, before)
            catalogue = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            owner = next(row for row in catalogue["requirements"] if row["id"] == rule)
            owner["oracle"] += "\n\n" + rule + " finite assumed-rank usage oracle: duplicate"
            with self.assertRaisesRegex(ValueError, "duplicate owned"):
                generated.synced_catalogue(catalogue)

    def test_usage_and_runtime_generators_compose_without_reordering_foreign_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (generated.CATALOGUE, generated.VIEW):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            path = root / generated.VIEW
            text = path.read_text()
            anchor = "The catalogue is `doc/catalogues/assumed_rank_8_5_8_7.json`.\n"
            path.write_text(text.replace(anchor, anchor + "\nForeign source narrative remains independently managed.\n"))
            generated.generate(root, sync_catalogue=True)
            rank_effects.generate(root, sync_catalogue=True)
            foreign = root / "tests/fixtures/assumed_rank_usage_foreign"
            foreign.mkdir()
            (foreign / "source.f90").write_text("Foreign author bytes.\n")
            before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
            with patch.object(runner, "run", side_effect=AssertionError("generation must not run a compiler")):
                for generators in ((generated, rank_effects), (rank_effects, generated)):
                    for module in generators:
                        module.generate(root, sync_catalogue=True)
                    for module in generators:
                        module.generate(root, check=True)
            self.assertEqual({path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}, before)
            for row in json.loads((root / generated.CATALOGUE).read_text())["requirements"]:
                self.assertIn(render_requirement(row), (root / generated.VIEW).read_text())

    def test_rule_specific_fingerprints_preserve_other_owner_runtime_cases_and_raw_evidence(self):
        protected = {path: (ROOT / path).read_bytes() for path in (
            "tests/reviews.json", "tests/expected_failures.txt", "doc/evidence/canonical_case_links.json",
            "doc/evidence/source_uses.json", "doc/evidence/whole_suite_execution.json")}
        for rule in ("C839", "C840"):
            registry = Registry(ROOT)
            source = registry.catalogues[generated.SECTION]
            source.update(review_state="reviewed", review_fingerprint=registry.catalogue_fingerprint(generated.SECTION),
                          review_rationale="In-memory lifecycle premise, never a persisted approval.")
            before = {case.name: case.fingerprint(registry) for case in self.all_cases}
            registry.requirements[rule]["oracle_limitation"] += " Independent changed source gate."
            changed = {case.name for case in self.all_cases if case.fingerprint(registry) != before[case.name]}
            self.assertEqual(changed, {case.name for case in self.all_cases if case.rule == rule})
            self.assertEqual(registry.catalogue_review_state(generated.SECTION), "stale")
        generated.generate(ROOT, check=True)
        rank_effects.generate(ROOT, check=True)
        self.assertEqual({path: (ROOT / path).read_bytes() for path in protected}, protected)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
