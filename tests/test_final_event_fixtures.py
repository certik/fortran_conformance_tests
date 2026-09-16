"""Ordinary event fixtures and independently enumerated timing/observer countermodels."""
import copy
import hashlib
import itertools
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_final_event_fixtures as generated
import generate_final_process_fixtures as process


EXPECTED = {
    1: {
        "assignment_order": [[], [(5, 11), (10, 7)]],
        "unallocated_left": [[], [], [(10, 1)]],
        "allocated_reallocation": [
            [], [(10, 2), (11, 7), (11, 11)],
            [(10, 2), (11, 7), (11, 11), (10, 3), (11, 17), (11, 19), (11, 23)],
        ],
        "allocated_subobject": [[], [(10, 7), (11, 2), (12, 17), (12, 19)]],
    },
    3: {
        "return_local": [[], [(10, 17)]],
        "end_local": [[], [(10, 19)]],
        "multiple_locals": [[], [(10, 17), (10, 19)]],
        "saved_local": [[], [(10, 17)]],
    },
    4: {
        "end_block": [[], [(10, 17)]],
        "nested_blocks": [[], [(10, 19)], [(10, 19), (10, 17)]],
        "saved_block": [[], [(10, 17)]],
    },
    5: {
        "statement_result": [[(5, 17)], [(5, 17), (20, 17), (10, 17)]],
        "if_result": [
            [(5, 1)], [(5, 1), (20, 1), (40, 31)],
            [(5, 1), (20, 1), (40, 31), (40, 37)],
            [(5, 1), (20, 1), (40, 31), (40, 37), (10, 1)],
        ],
        "do_result": [
            [(5, 3)], [(5, 3), (20, 3)], [(5, 3), (20, 3)], [(5, 3), (20, 3)],
            [(5, 3), (20, 3), (10, 3), (41, 4)],
        ],
        "pointer_result": [
            [(5, 23)], [(5, 23), (20, 23)], [(5, 23), (20, 23), (10, 23)],
        ],
    },
    7: {
        "ordinary_out": [
            [(10, 7), (11, 9)], [(10, 7), (11, 9), (20, 5)],
            [(10, 7), (11, 9), (20, 5), (10, 11), (11, 13)],
        ],
        "elemental_scalar": [
            [(10, 17), (20, 17), (10, 19), (20, 19)],
            [(10, 17), (20, 17), (10, 19), (20, 19), (30, 2), (31, 31), (31, 37)],
        ],
        "elemental_array_only": [
            [(20, 31), (20, 37)], [(20, 31), (20, 37), (30, 2), (31, 31), (31, 37)],
        ],
    },
}

FACETS = {
    1: {
        "assignment_order": ["old-value-before-definition", "rhs-evaluation-before-final"],
        "unallocated_left": ["unallocated-left-exclusion"],
        "allocated_reallocation": ["allocated-left-reallocation"],
        "allocated_subobject": ["allocated-subobject-before-release"],
    },
    3: {
        "return_local": ["explicit-return-local"],
        "end_local": ["end-subprogram-local"],
        "multiple_locals": ["multiple-locals-unordered"],
        "saved_local": ["saved-local-exclusion-control"],
    },
    4: {
        "end_block": ["ordinary-end-block"],
        "nested_blocks": ["nested-block-timing"],
        "saved_block": ["saved-block-exclusion-control"],
    },
    5: {
        "statement_result": ["statement-result-boundary"],
        "if_result": ["if-construct-boundary"],
        "do_result": ["do-control-boundary"],
        "pointer_result": ["pointer-result-exclusion-control"],
    },
    7: {
        "ordinary_out": ["ordinary-intent-out-old-value"],
        "elemental_scalar": ["elemental-scalar-selection"],
        "elemental_array_only": ["elemental-array-only-no-entry-final"],
    },
}


class FinalEventFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {c.name: c for c in all_cases if "/fixtures/final_event_" in c.path}
        cls.catalogue = cls.registry.catalogues["7.5.6.3"]

    def name(self, group, variant):
        return generated.identifier(f"S7.5.6.3-{group:03}", variant)

    def spec(self, group, variant):
        return self.specs[self.name(group, variant)]

    def source(self, group, variant):
        return (self.cases[self.name(group, variant)].fixture.root / "source.f90").read_text()

    def accepts(self, group, variant, traces):
        return generated.history_accepts(self.spec(group, variant), traces)

    def test_exact_ids_primary_facets_metadata_and_phase(self):
        names = {self.name(group, v) for group, variants in EXPECTED.items() for v in variants}
        self.assertEqual(len(names), 18)
        self.assertEqual(set(self.cases), names)
        self.assertEqual(set(self.specs), names)
        self.assertEqual(sum(len(s["observations"]) for s in self.specs.values()), 44)
        self.assertEqual(sum(len(generated.expanded_observations(s)) for s in self.specs.values()), 46)
        for group, variants in FACETS.items():
            for variant, facets in variants.items():
                case = self.cases[self.name(group, variant)]
                with self.subTest(case=case.name):
                    self.assertEqual(case.rule, f"S7.5.6.3-{group:03}")
                    self.assertEqual(case.meta.facets, facets)
                    self.assertEqual(case.kind, "valid")
                    self.assertEqual(case.fixture.expectation.phase, "run")
                    self.assertEqual(case.fixture.expectation.outcome, "success")
                    self.assertEqual(case.fixture.expectation.exit_code, 0)
                    self.assertEqual(case.meta.evidence, "effect")
                    self.assertEqual(case.meta.standard, "f2023")
                    self.assertEqual(case.meta.oracle_basis, "standard")
                    self.assertFalse(case.meta.profiles)
                    self.assertFalse(case.meta.coarray)
                    self.assertEqual(case.meta.images, 1)
                    self.assertEqual(self.registry.requirements[case.rule]["category"], "effect")
                    self.assertEqual(self.specs[case.name]["facets"], facets)
                    self.assertEqual([o["expected"] for o in generated.expanded_observations(self.specs[case.name])],
                                     EXPECTED[group][variant])
        selected = runner.select_cases(list(self.cases.values()), sorted(names))
        self.assertEqual({c.name for c in selected}, names)

    def test_exact_generated_bytes_guard_ranges_and_owned_namespace(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("final_event_*/*") if p.is_file()}
        self.assertEqual(set(self.outputs), actual)
        self.assertEqual(len(actual), 36)
        for path, content in self.outputs.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), content)
                self.assertTrue(path.relative_to(ROOT).as_posix().startswith("tests/fixtures/final_event_"))
                content.decode("ascii")
                if path.suffix == ".f90":
                    self.assertLessEqual(max(map(len, content.splitlines())), 132)
        for name, spec in self.specs.items():
            text = (self.cases[name].fixture.root / "source.f90").read_text()
            self.assertEqual(text.split("module final_types\n", 1)[0], process.LOG_MODULE)
            self.assertEqual(generated.bind_observations(text, spec["observations"]), spec["oracle_guards"])
            self.assertEqual(text.count("! checkpoint: "), len(spec["observations"]))
            for obs, guard in zip(spec["observations"], spec["oracle_guards"]):
                code = "\n".join(text.splitlines()[guard["line"]-1:guard["end_line"]]) + "\n"
                self.assertEqual(code, generated.observation_code(obs))
                self.assertEqual(hashlib.sha256(code.encode()).hexdigest(), guard["sha256"])

    def test_exact_pending_partition_and_complete_appendix(self):
        coverage = {}
        for spec in self.specs.values():
            coverage.setdefault(spec["rule"], set()).update(spec["facets"])
        independent = {f"S7.5.6.3-{g:03}": {f for fs in variants.values() for f in fs}
                       for g, variants in FACETS.items()}
        self.assertEqual(coverage, independent)
        self.assertEqual(sum(map(len, coverage.values())), 19)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 33)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 14)
        for requirement in self.catalogue["requirements"]:
            self.assertEqual(set(requirement["pending"]),
                             set(requirement["facets"]) - coverage.get(requirement["id"], set()))
            self.assertEqual(requirement["diagnostic_obligation"], "not-required")
            self.assertEqual(requirement["category"], "effect")
        for group, count in [(2, 6), (6, 3)]:
            requirement = self.registry.requirements[f"S7.5.6.3-{group:03}"]
            self.assertEqual(len(requirement["pending"]), count)
            self.assertNotIn("Finite ordinary-event implementation:", requirement["oracle"])
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue, self.specs))
        appendix = view.split("## Complete finite pending plans\n", 1)[1].split(
            "## Reproduction and remaining gates", 1)[0]
        self.assertEqual(appendix.count("* **`"), 14)
        for r in self.catalogue["requirements"]:
            for facet, plan in r["pending"].items():
                self.assertIn(f"* **`{facet}`** - {plan}", appendix)

    def test_catalogue_sync_and_review_rendering_preserve_administration(self):
        self.assertEqual(generated.synced_catalogue(self.catalogue, self.specs), self.catalogue)
        reviewed = copy.deepcopy(self.catalogue)
        reviewed["review_state"] = "reviewed"
        reviewed["review_rationale"] = "Synthetic in-memory state test, not an approval."
        registry = Registry(ROOT)
        registry.catalogues[generated.SECTION] = reviewed
        reviewed["review_fingerprint"] = registry.catalogue_fingerprint(generated.SECTION)
        self.assertEqual(generated.synced_catalogue(reviewed, self.specs), reviewed)
        self.assertIn("Catalogue source review: reviewed.", generated.render_view(reviewed, self.specs))
        reviewed["review_fingerprint"] = "0" * 64
        self.assertIn("Catalogue source review: stale.", generated.render_view(reviewed, self.specs))
        self.assertEqual(generated.synced_catalogue(reviewed, self.specs), reviewed)

    def test_independent_correct_histories_and_nonvacuous_observers(self):
        for group, variants in EXPECTED.items():
            for variant, expected in variants.items():
                with self.subTest(group=group, variant=variant):
                    self.assertTrue(self.accepts(group, variant, expected))
                    self.assertFalse(self.accepts(group, variant, [[] for _ in expected]))
                    self.assertFalse(self.accepts(group, variant, expected[:-1]))
                    self.assertFalse(self.accepts(group, variant, expected + [expected[-1]]))
                    missing_finals = [[e for e in stage if e[0] not in (10, 30)] for stage in expected]
                    self.assertFalse(self.accepts(group, variant, missing_finals))

    def test_every_guard_rejects_missing_duplicate_wrong_and_extra_events(self):
        probes = 0
        for group, variants in EXPECTED.items():
            for variant, histories in variants.items():
                for position, expected in enumerate(histories):
                    obs = generated.expanded_observations(self.spec(group, variant))[position]
                    for i, event in enumerate(expected):
                        for wrong in (
                            expected[:i] + expected[i+1:], expected + [event],
                            expected[:i] + [(event[0], event[1]+1000)] + expected[i+1:],
                            expected[:i] + [(event[0]+1000, event[1])] + expected[i+1:],
                        ):
                            self.assertFalse(generated.model_accepts(obs["expected"], obs["before"], wrong))
                            history = copy.deepcopy(histories)
                            history[position] = wrong
                            self.assertFalse(self.accepts(group, variant, history))
                            probes += 1
                    self.assertFalse(generated.model_accepts(
                        obs["expected"], obs["before"], expected + [(999, 999)]))
                    probes += 1
        self.assertEqual(probes, 402)

    def test_assignment_evaluation_old_value_and_separate_cleanup_countermodels(self):
        for wrong in [[(10, 7), (5, 11)], [(5, 11), (10, 11)],
                      [(5, 11)], [(5, 11), (10, 7), (10, 11)]]:
            self.assertFalse(self.accepts(1, "assignment_order", [[], wrong]))
        self.assertFalse(self.accepts(1, "unallocated_left", [[], [(10, 1)], [(10, 1)]]))
        self.assertFalse(self.accepts(1, "unallocated_left", [[], [], []]))
        reallocation = copy.deepcopy(EXPECTED[1]["allocated_reallocation"])
        for wrong in [[(10, 3), (11, 17), (11, 19), (11, 23)],
                      [(10, 0)], [(10, 2), (11, 7), (11, 7)]]:
            mutated = copy.deepcopy(reallocation)
            mutated[1] = wrong
            self.assertFalse(self.accepts(1, "allocated_reallocation", mutated))
        subobject = EXPECTED[1]["allocated_subobject"]
        for wrong in [[(10, 7)], [(10, 11), (11, 3), (12, 31), (12, 37), (12, 41)],
                      [(10, 7), (11, 0)]]:
            self.assertFalse(self.accepts(1, "allocated_subobject", [subobject[0], wrong]))

    def test_multiple_locals_accept_both_orders_without_alias_or_declaration_order(self):
        expected = [(10, 17), (10, 19)]
        for order in itertools.permutations(expected):
            self.assertTrue(self.accepts(3, "multiple_locals", [[], list(order)]))
        for wrong in [[], [(10, 17)], [(10, 17), (10, 17)], expected + [(10, 19)]]:
            self.assertFalse(self.accepts(3, "multiple_locals", [[], wrong]))
        for group, variant in [(3, "saved_local"), (4, "saved_block")]:
            self.assertFalse(self.accepts(group, variant, [[], [(10, 17), (10, 41)]]))
            self.assertFalse(self.accepts(group, variant, [[], [(10, 41)]]))
            self.assertFalse(self.accepts(group, variant, [[(10, 17)], [(10, 17)]]))

    def test_nested_block_and_construct_result_timing_countermodels(self):
        for wrong in [
            [[], [], [(10, 19), (10, 17)]],
            [[], [(10, 19), (10, 17)], [(10, 19), (10, 17)]],
            [[], [(10, 17)], [(10, 17), (10, 19)]],
        ]:
            self.assertFalse(self.accepts(4, "nested_blocks", wrong))
        for variant, token in [("statement_result", 17), ("if_result", 1), ("do_result", 3)]:
            expected = EXPECTED[5][variant]
            for position in range(len(expected)-1):
                early = copy.deepcopy(expected)
                early[position].append((10, token))
                self.assertFalse(self.accepts(5, variant, early))
            late = copy.deepcopy(expected)
            late[-1].remove((10, token))
            self.assertFalse(self.accepts(5, variant, late))
        expected = EXPECTED[5]["do_result"]
        for index in [0, 1, 2, 3, 5]:
            wrong = copy.deepcopy(expected)
            wrong[-1][-1] = (41, index)
            self.assertFalse(self.accepts(5, "do_result", wrong))
        self.assertFalse(self.accepts(5, "do_result", [expected[0], expected[-1]]))

    def test_pointer_result_exclusion_cannot_be_masked_by_later_assignment(self):
        expected = EXPECTED[5]["pointer_result"]
        early = copy.deepcopy(expected)
        early[1].append((10, 23))
        self.assertFalse(self.accepts(5, "pointer_result", early))
        no_positive = copy.deepcopy(expected)
        no_positive[-1].remove((10, 23))
        self.assertFalse(self.accepts(5, "pointer_result", no_positive))
        text = self.source(5, "pointer_result")
        self.assertIn("impure function locate() result(value)", text)
        self.assertIn("type(item), target, save :: saved_target", text)
        self.assertIn("value=>saved_target", text)
        self.assertNotIn("deallocate(", text)
        self.assertEqual(self.spec(5, "pointer_result")["whole_assignments"],
                         ["saved_target=item(token=29)"])

    def test_ordinary_out_old_default_body_and_cleanup_are_separate(self):
        expected = EXPECTED[7]["ordinary_out"]
        for wrong in [[], [(10, 11), (11, 13)], [(10, 7), (11, 5)]]:
            history = copy.deepcopy(expected)
            history[0] = wrong
            self.assertFalse(self.accepts(7, "ordinary_out", history))
        wrong = copy.deepcopy(expected)
        wrong[1] = wrong[-1]
        self.assertFalse(self.accepts(7, "ordinary_out", wrong))
        text = self.source(7, "ordinary_out")
        body = text.split("subroutine define_out(self)\n", 1)[1].split("end subroutine define_out", 1)[0]
        self.assertLess(body.index("call expect_log"), body.index("if (self%defaulted/=5)"))
        self.assertLess(body.index("self%token=11"), body.index("self%defaulted=13"))
        self.assertNotRegex(body, r"(?im)^.*(?:if|call).*self%token")
        self.assertIn("19.6.5(24)", self.spec(7, "ordinary_out")["premises"])

    def test_elemental_entry_accepts_only_per_element_before_edges(self):
        events = EXPECTED[7]["elemental_scalar"][0]
        suffix = [(30, 2), (31, 31), (31, 37)]
        accepted = 0
        for order in itertools.permutations(events):
            legal = (order.index((10, 17)) < order.index((20, 17))
                     and order.index((10, 19)) < order.index((20, 19)))
            self.assertEqual(self.accepts(7, "elemental_scalar", [list(order), list(order)+suffix]), legal)
            accepted += legal
        self.assertEqual(accepted, 6)
        self.assertEqual(self.spec(7, "elemental_scalar")["entry_edges"],
                         [((10, 17), (20, 17)), ((10, 19), (20, 19))])
        self.assertFalse(self.accepts(7, "elemental_scalar",
                                    [[(30, 2), (31, 17), (31, 19), (20, 17), (20, 19)],
                                     EXPECTED[7]["elemental_scalar"][1]]))
        text = self.source(7, "elemental_scalar")
        self.assertIn("call define_out(actual,[17,19],[31,37])", text)
        self.assertIn("call expect_before(10,old_token,20,old_token)", text)
        self.assertNotIn("actual%token,", text)
        self.assertNotIn("self%token)", text.split("impure elemental subroutine define_out", 1)[1]
                         .split("end subroutine define_out", 1)[0])
        self.assertIn("impure elemental subroutine finish_each(self)", text)
        self.assertIn("type(item), intent(inout) :: self(:)", text)

    def test_array_only_exclusion_requires_body_and_real_rank_one_cleanup(self):
        expected = EXPECTED[7]["elemental_array_only"]
        for early in [(30, 2), (10, 17), (10, 19)]:
            wrong = copy.deepcopy(expected)
            wrong[0].append(early)
            self.assertFalse(self.accepts(7, "elemental_array_only", wrong))
        for wrong in [expected[0], [], expected[0]+[(10, 31), (10, 37)]]:
            self.assertFalse(self.accepts(7, "elemental_array_only", [expected[0], wrong]))
        text = self.source(7, "elemental_array_only")
        self.assertEqual(re.findall(r"(?m)^final :: (.*)$", text), ["finish_array"])
        self.assertNotIn("extends(", text)
        self.assertEqual(len(re.findall(r"(?m)^type :: ", text)), 1)
        self.assertIn("impure elemental subroutine define_out(self,new_token)", text)
        self.assertIn("if (array_finals/=0) error stop 155", text)
        self.assertIn("self%token=new_token", text)
        self.assertLess(text.index("! checkpoint: array-only-after-call"), text.index("deallocate(actual"))

    def test_cumulative_histories_cannot_rewrite_past_log_entries(self):
        first = EXPECTED[7]["elemental_scalar"][0]
        rewritten = [(10, 19), (20, 19), (10, 17), (20, 17), (30, 2), (31, 31), (31, 37)]
        spec = self.spec(7, "elemental_scalar")
        self.assertTrue(generated.case_accepts(spec["observations"], [first, rewritten]))
        self.assertFalse(generated.history_accepts(spec, [first, rewritten]))

    def test_source_premises_exclude_setup_finals_and_invalid_final_signatures(self):
        total_assignments = 0
        for name, case in self.cases.items():
            text = (case.fixture.root / "source.f90").read_text()
            spec = self.specs[name]
            declarations = re.findall(r"(?im)^type\(item\)(?:,[^:]*)?\s*::\s*(.*)$", text)
            record_names = {part.split("(")[0].strip() for declaration in declarations
                            for part in declaration.split(",")}
            assignments = [line for line in text.splitlines() if any(
                re.match(rf"^{variable}(?:\([^)]*\))?=(?!=|>)", line) for variable in record_names)]
            self.assertEqual(assignments, spec["whole_assignments"], name)
            total_assignments += len(assignments)
            self.assertEqual(text.count("call reset_log()"), 1)
            self.assertNotRegex(text, r"(?im)^type\(item\).*::.*=(?!>)")
            self.assertNotRegex(text, r"(?im)^class\(")
            finals = re.findall(r"(?m)^final :: (.*)$", text)
            self.assertTrue(finals)
            for routine in finals:
                self.assertNotIn("call " + routine + "(", text)
                signature = re.search(
                    rf"(?m)^(?:impure elemental )?subroutine {routine}\(self\)\n([^\n]+)", text)
                self.assertIsNotNone(signature)
                self.assertRegex(signature[1], r"^type\(item\), intent\(inout\) :: self(?:\(:\))?$")
            self.assertNotRegex(text, r"(?im)^(?!impure )elemental ")
            self.assertNotIn("do concurrent", text)
            self.assertNotIn("error stop 77", text)
            self.assertNotIn("stop 200", text)
            self.assertNotIn("interface item", text)
            self.assertNotIn("assignment(=)", text)
        self.assertEqual(total_assignments, 5)

    def test_allocation_and_lifetime_inquiries_are_guarded(self):
        text = self.source(1, "allocated_subobject")
        callback = text.split("subroutine finish_scalar(self)\n", 1)[1].split(
            "end subroutine finish_scalar", 1)[0]
        self.assertLess(callback.index("if (.not.allocated(self%child))"),
                        callback.index("size(self%child)"))
        text = self.source(1, "unallocated_left")
        callback = text.split("subroutine finish_scalar(self)\n", 1)[1].split(
            "end subroutine finish_scalar", 1)[0]
        self.assertNotIn("self%", callback)
        for name, case in self.cases.items():
            text = (case.fixture.root / "source.f90").read_text()
            for line in text.splitlines():
                if re.match(r"^(?:deallocate|allocate)\(", line):
                    self.assertIn(",stat=status)", line, name)
            for line in re.findall(r"(?m)^allocate\([^\n]+\n[^\n]+\n[^\n]+", text):
                self.assertIn("if (status/=0) error stop 111", line)
                self.assertIn("if (.not.allocated(", line)
        nested = self.source(4, "nested_blocks").split("! checkpoint: nested-between", 1)[1]
        self.assertNotIn("inner%", nested)
        for variant in ["return_local", "end_local", "multiple_locals", "saved_local"]:
            caller = self.source(3, variant).split("program p\n", 1)[1]
            self.assertNotRegex(caller, r"(?:first|second|kept)%")

    def test_original_process_corpus_remains_byte_exact_and_disjoint(self):
        outputs, specs = process.build_corpus()
        self.assertEqual((len(specs), len(outputs)), (17, 34))
        self.assertFalse(set(outputs) & set(self.outputs))
        for path, expected in outputs.items():
            self.assertEqual(path.read_bytes(), expected)


if __name__ == "__main__":
    unittest.main()
