"""C877 NAME presence, shared repair, exact causes and independent lifecycle state."""
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
from suite_data import Registry, render_requirement, validate_case_requirement, write_json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_bind_name_cardinality_fixtures as generated

FAMILIES = (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))


class BindNameCardinalityFixturesTests(unittest.TestCase):
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

    def case(self, variant):
        return self.cases[generated.identifier(variant)]

    def test_three_exact_cases_two_exclusion_facets_and_one_shared_compile_control(self):
        self.assertEqual(set(self.cases), {
            "C877_invalid__bind_empty_name_two_variables",
            "C877_invalid__bind_blank_name_two_variables",
            "C877_valid__bind_no_name_shared_control",
        })
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 6)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets}, set(generated.FACETS))
        controls = [case for case in self.cases.values() if case.kind == "valid"]
        self.assertEqual([case.name for case in controls], [generated.identifier("control")])
        self.assertEqual(controls[0].meta.facets, list(generated.FACETS))
        for case in self.cases.values():
            self.assertEqual((case.rule, case.meta.standard, case.meta.oracle_basis), ("C877", "f2023", "standard"))
            invalid = case.kind == "invalid"
            self.assertEqual(case.meta.evidence, "effect" if invalid else "positive-control")
            self.assertEqual(self.members[case.name]["cohort"], "diagnostic-only" if invalid else "positive-control")
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            self.assertIsNone(case.fixture.link)
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.step), ("compile", "source"))
            self.assertEqual(case.fixture.expectation.outcome, "diagnose" if invalid else "success")

    def test_both_repairs_delete_only_name_clause_and_converge_byte_for_byte(self):
        control = (self.case("control").fixture.root / "source.f90").read_bytes()
        self.assertEqual(control.count(b"bind(c)"), 1)
        self.assertNotIn(b"name=", control)
        for variant, value in (("empty", ""), ("blank", "   ")):
            case = self.case(variant)
            spec = self.specs[case.name]
            raw = (case.fixture.root / "source.f90").read_bytes()
            repair = spec["repair"]
            start, end = repair["span"]
            self.assertEqual(raw[start:end].decode(), ", name='" + value + "'")
            self.assertEqual(raw[:start] + raw[end:], control)
            self.assertEqual(repair["control_id"], generated.identifier("control"))
            self.assertEqual(repair["control_sha256"], generated.sha(control))
            self.assertEqual(spec["name_value"], value)
            self.assertEqual(spec["name_value"].strip(), "")
            self.assertEqual([n + 1 for n, (a, b) in enumerate(zip(raw.splitlines(), control.splitlines()))
                              if a != b], [5])
            self.assertEqual(len(raw.splitlines()), len(control.splitlines()))
        self.assertEqual(self.specs[generated.identifier("control")]["shared_by"],
                         [generated.identifier("empty"), generated.identifier("blank")])

    def test_complete_module_has_guaranteed_kind_and_no_other_role_or_label_conflict(self):
        for spec in self.specs.values():
            source = spec["source"]
            lines = source.splitlines()
            self.assertEqual(len(lines), 6)
            self.assertEqual(lines[:4], [
                "module bind_name_cardinality_scope",
                "  use, intrinsic :: iso_c_binding, only: c_int",
                "  implicit none",
                "  integer(c_int) :: first_value, second_value"])
            self.assertEqual(lines[-1], "end module bind_name_cardinality_scope")
            self.assertTrue(lines[4].endswith(" :: first_value, second_value"))
            self.assertEqual(source.count("bind(c"), 1)
            self.assertNotRegex(source, r"(?i)\b(common|save|pointer|allocatable|parameter|call|print|"
                                       r"allocate|subroutine|function|target|volatile|optional)\b")
            self.assertNotIn("[", source)
            self.assertNotIn("\r", source)
            source.encode("ascii")
            self.assertLessEqual(max(map(len, lines)), 132)

    def test_exact_measured_cause_has_one_live_statement_interval_and_no_warning_allowance(self):
        for variant in ("empty", "blank"):
            diagnostic = self.case(variant).fixture.expectation.diagnostic
            self.assertEqual((diagnostic["file"], diagnostic["line"], diagnostic["end_line"]), ("source.f90", 5, 5))
            self.assertEqual(diagnostic["equals_any"], [generated.CAUSE])
            for field in ("contains_any", "allow_nonfatal", "additional_spans"):
                self.assertNotIn(field, diagnostic)

    def staged(self, case, family, *, cause=generated.CAUSE, code=1, line=5, end_line=None,
               filename=None, severity="error", silent=False, echo=False, tail="",
               timeout=False, codes=False, printed_code=False):
        comp = runner.Compiler(family, family, dict(FAMILIES)[family], "synthetic transport, not calibration")
        raw = (case.fixture.root / "source.f90").read_bytes()
        calls = []

        def transport(command, cwd, wait, stdin=None):
            source = Path(command[command.index("-c") + 1])
            self.assertEqual((source.parent, source.name), (Path(cwd).resolve(), "source.f90"))
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual((command[0], wait, stdin), (family, 5, None))
            location = str(source) if filename is None else filename
            shown = raw.decode().splitlines()[4]
            actual = "syntax error" if echo else cause
            if family == "lfortran":
                tag = " [C877]" if printed_code else ""
                text = f"{location}:{line}-{line if end_line is None else end_line}:1-80: semantic {severity}{tag}: {actual}\n"
            elif family == "gfortran":
                text = (f"{location}:{line}:{len(shown) + 1}:\n\n {line:4} | {shown}\n"
                        f"      | {' ' * len(shown)}1\n{severity.capitalize()}: {actual}\n")
            else:
                text = f"{location}:{line}:3: {severity}: {actual}\n  {shown}\n    ^\n"
            if echo:
                text += f"    5 | ! {cause}\n      | 1\n"
            text = "" if silent else text + tail
            calls.append(list(command))
            return runner.ProcessResult(code, text, timeout, "", text, b"", text.encode())

        with patch.object(runner, "run", side_effect=transport):
            check = runner.check_fixture(case.fixture, comp, timeout=5, codes=codes)
        self.assertEqual((len(calls), len(check.trace), check.phase), (1, 1, "compile"))
        self.assertEqual(check.input_hashes, {"source.f90": generated.sha(raw)})
        self.assertFalse(validate_case_trace(self.members[case.name], asdict(check),
                                            dict(comp.configuration(), version=comp.version), ROOT, None, False))
        type(self).transport_vectors += 1
        return check

    def test_complete_error_cause_does_not_need_fatal_status_or_a_printed_code(self):
        for variant, (family, _), status in itertools.product(("empty", "blank"), FAMILIES, (0, 1, 2)):
            self.assertEqual(self.staged(self.case(variant), family, code=status).outcome, "pass")
        for variant in ("empty", "blank"):
            self.assertEqual(self.staged(self.case(variant), "lfortran", codes=True).outcome, "fail")
            self.assertEqual(self.staged(self.case(variant), "lfortran", codes=True, printed_code=True).outcome, "pass")

    def test_partial_wrong_condition_wrapped_quoted_and_echoed_messages_do_not_qualify(self):
        wrong = (
            "NAME", "identifier", "Multiple identifiers", "single NAME= specifier",
            "Duplicate global binding label", "Invalid binding label",
            "Empty NAME is not supported", "BIND statements are not supported",
            "C_INT is not defined", "A BIND variable must be declared in a module",
            "Unrelated condition: " + generated.CAUSE, generated.CAUSE + " (example)",
            'Example: "' + generated.CAUSE + '"', 'Unknown symbol "' + generated.CAUSE + '"',
        ) + tuple(prefix + generated.CAUSE for prefix in
                  ("Unsupported: ", "Not implemented: ", "Internal: ", "Recovery: "))
        for variant, (family, _) in itertools.product(("empty", "blank"), FAMILIES):
            case = self.case(variant)
            for cause in wrong:
                self.assertEqual(self.staged(case, family, cause=cause).outcome, "fail")
            self.assertEqual(self.staged(case, family, echo=True).outcome, "fail")

    def test_only_actual_statement_origin_qualifies_and_silence_is_failure(self):
        for variant, (family, _) in itertools.product(("empty", "blank"), FAMILIES):
            case = self.case(variant)
            for filename in (None, "source.f90", "./source.f90"):
                self.assertEqual(self.staged(case, family, filename=filename).outcome, "pass")
            for filename in ("foreign.f90", "/unrelated/source.f90", "missing/source.f90"):
                self.assertEqual(self.staged(case, family, filename=filename).outcome, "fail")
            for line in (1, 4, 6):
                self.assertEqual(self.staged(case, family, line=line).outcome, "fail")
            if family == "lfortran":
                self.assertEqual(self.staged(case, family, line=4, end_line=5).outcome, "fail")
                self.assertEqual(self.staged(case, family, end_line=6).outcome, "fail")
            for status in (0, 1):
                self.assertEqual(self.staged(case, family, code=status, silent=True).outcome, "fail")
                self.assertEqual(self.staged(case, family, code=status, severity="warning").outcome, "fail")
            self.assertEqual(self.staged(case, family, timeout=True).outcome, "fail")
            for status in (-11, 139):
                self.assertEqual(self.staged(case, family, code=status).outcome, "fail")
            for tail in ("\nASR verify pass error\n",
                         "\n/unrelated/foreign.f90:1:1: error: Internal: compiler failure\n",
                         "\nf951: Fatal Error: out of memory\n"):
                self.assertEqual(self.staged(case, family, tail=tail).outcome, "fail")

    def test_shared_control_executes_only_one_compile_and_requires_object_production(self):
        case = self.case("control")
        for (family, mode), fault in itertools.product(FAMILIES, (None, "missing-object", "error", "internal", "timeout")):
            comp = runner.Compiler(family, family, mode, "synthetic transport")
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
                check = runner.check_fixture(case.fixture, comp, timeout=5)
            self.assertEqual(check.outcome, "pass" if fault is None else "fail")
            self.assertEqual((len(calls), len(check.trace), check.phase), (1, 1, "compile"))
            type(self).transport_vectors += 1

    def test_unselected_facets_other_owners_and_raw_review_states_are_preserved(self):
        original = self.registry.catalogues[generated.SECTION]
        others = sorted(set(self.registry.requirements[generated.RULE]["facets"]) - set(generated.FACETS))
        for owned_mask, foreign_mask, state in itertools.product(range(4), range(1 << len(others)),
                                                                ("draft", "reviewed", "stale")):
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
            for row in candidate["requirements"]:
                if row["id"] != generated.RULE:
                    row["pending"] = {} if owned_mask & 1 else {f: "Foreign pending: " + f for f in row["facets"]}
            owner["oracle"] += "\n\nForeign oracle."
            owner["oracle_limitation"] += "\n\nForeign limitation."
            candidate.update(review_state="draft" if state == "draft" else "reviewed",
                             review_fingerprint=("0" if state == "stale" else "1") * 64,
                             review_rationale="Synthetic raw state, not an approval.")
            before, expected = copy.deepcopy(candidate), copy.deepcopy(candidate)
            target = next(row for row in expected["requirements"] if row["id"] == generated.RULE)
            for facet in generated.FACETS:
                target["pending"].pop(facet, None)
            actual = generated.synced_catalogue(candidate)
            self.assertEqual(candidate, before)
            self.assertEqual(actual, expected)
            self.assertEqual(generated.synced_catalogue(actual), actual)
            self.assertTrue(all(render_requirement(row) in generated.render_view(actual) for row in actual["requirements"]))
            type(self).generator_state_vectors += 1

    def test_selected_definitions_and_unique_owned_paragraphs_are_required(self):
        for facet in generated.FACETS:
            candidate = copy.deepcopy(self.registry.catalogues[generated.SECTION])
            owner = next(row for row in candidate["requirements"] if row["id"] == generated.RULE)
            owner["facets"].remove(facet)
            before = copy.deepcopy(candidate)
            with self.assertRaisesRegex(ValueError, "selected C877 facet definitions"):
                generated.synced_catalogue(candidate)
            self.assertEqual(candidate, before)
        candidate = copy.deepcopy(self.registry.catalogues[generated.SECTION])
        next(row for row in candidate["requirements"] if row["id"] == generated.RULE)["oracle"] += (
            "\n\n" + generated.ORACLE_PREFIX + "duplicate")
        with self.assertRaisesRegex(ValueError, "duplicate owned"):
            generated.synced_catalogue(candidate)

    def test_standalone_generator_preserves_foreign_fixture_and_narrative_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in (generated.CATALOGUE, generated.VIEW):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / relative).read_bytes())
            path = root / generated.VIEW
            path.write_text("Foreign exact preface.\n\n" + path.read_text())
            generated.generate(root, sync_catalogue=True)
            foreign = root / "tests/fixtures/bind_name_cardinality_foreign"
            foreign.mkdir()
            (foreign / "source.f90").write_text("Foreign bytes.\n")
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with patch.object(runner, "run", side_effect=AssertionError("generation must not run a compiler")):
                for _ in range(2):
                    generated.generate(root, sync_catalogue=True)
                    generated.generate(root, check=True)
            self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}, before)

    def test_own_requirement_change_stales_all_three_shared_control_bindings_only(self):
        registry = Registry(ROOT)
        before = {case.name: case.fingerprint(registry) for case in self.all_cases}
        registry.requirements[generated.RULE]["oracle_limitation"] += " Changed current owner gate."
        changed = {case.name for case in self.all_cases if case.fingerprint(registry) != before[case.name]}
        self.assertEqual(changed, {case.name for case in self.all_cases if case.rule == generated.RULE})
        self.assertTrue(set(self.cases) <= changed)
        for case in self.cases.values():
            validate_case_requirement(case, self.registry.requirements[generated.RULE])
        self.assertEqual(len({case.review_key for case in self.cases.values()}), 3)

    def test_generated_inputs_and_check_only_render_are_exact(self):
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)
        self.registry.render()
        self.assertEqual(generated.build_corpus()[0], self.files)


if __name__ == "__main__":
    unittest.main()
