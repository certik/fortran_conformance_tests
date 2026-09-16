"""Executable process inputs plus independent finite order/multiplicity countermodels."""
from collections import Counter
import itertools
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_final_process_fixtures as generated
import generate_derived_parameter_fixtures as parameters


CASES = {
    "S7.5.6.2-001": {
        "scalar": [[(10, 17)]],
        "array_exact": [[(10, 2), (11, 17), (11, 19)],
                        [(20, 4), (21, 23), (21, 29), (21, 31), (21, 37)], [(10, 0)]],
        "kind_tuple": [[(101, 11), (901, 3), (902, 5)], [(102, 13), (901, 7), (902, 9)],
                       [(201, 17), (901, 4), (902, 6)], [(202, 19), (901, 8), (902, 10)],
                       [(101, 23), (901, 12), (902, 14)]],
        "exact_before_elemental": [[(10, 2)], [(20, 17), (20, 19), (20, 23), (20, 29)], []],
        "assumed_rank": [[(50, 0), (60, 11)], [(50, 1), (60, 17), (60, 19)], [(50, 2)]],
        "no_own_match": [[(30, 17)]],
        "private_name": [[(10, 23)]],
    },
    "S7.5.6.2-002": {
        "plain_recursion": [[(20, 17)]],
        "siblings": [[(20, 11), (20, 13)]],
        "array_components": [[(10, 2), (20, 11), (20, 13), (30, 2), (30, 2),
                              (31, 21), (31, 23), (31, 25), (31, 27)]],
        "empty_outer": [[(10, 0)], [(10, 2), (20, 17), (20, 19)]],
        "pointer_exclusion": [[(10, 11)], [(20, 31)]],
    },
    "S7.5.6.2-003": {
        "own_before_components": [[(10, 1), (20, 11), (20, 13)]],
        "components_before_parent": [[(10, 1), (20, 11), (30, 21)]],
        "parent_without_child_final": [[(20, 11), (30, 21)]],
        "recursive_parent": [[(10, 1), (20, 11), (20, 13), (30, 21),
                              (20, 31), (20, 33), (40, 41)]],
    },
    "S7.5.6.2-004": {
        "independent_entities": [[(20, 17), (20, 19)]],
    },
}


class FinalProcessFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {c.name: c for c in all_cases if "/fixtures/final_process_" in c.path}
        cls.catalogue = cls.registry.catalogues["7.5.6.2"]

    def name(self, group, variant):
        return generated.identifier(f"S7.5.6.2-{group:03}", variant)

    def spec(self, group, variant):
        return self.specs[self.name(group, variant)]

    def source(self, group, variant):
        case = self.cases[self.name(group, variant)]
        return (case.fixture.root / "source.f90").read_text()

    def accepts(self, group, variant, trace, checkpoint=0):
        obs = self.spec(group, variant)["observations"][checkpoint]
        return generated.model_accepts(obs["expected"], obs["before"], trace)

    def test_exact_case_facets_phases_and_declared_observations(self):
        expected = {generated.identifier(rule, variant): observations
                    for rule, variants in CASES.items() for variant, observations in variants.items()}
        self.assertEqual(len(expected), 17)
        self.assertEqual(set(self.specs), set(expected))
        self.assertEqual(set(self.cases), set(expected))
        self.assertEqual(sum(len(x) for x in expected.values()), 29)
        for name, observations in expected.items():
            case = self.cases[name]
            spec = self.specs[name]
            with self.subTest(case=name):
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.meta.evidence,
                                 "positive-control" if case.rule == "S7.5.6.2-004" else "effect")
                self.assertEqual(case.meta.standard, "f2023")
                self.assertEqual(case.meta.oracle_basis, "standard")
                self.assertFalse(case.meta.profiles)
                self.assertFalse(case.meta.coarray)
                self.assertEqual(case.meta.images, 1)
                self.assertEqual([o["expected"] for o in spec["observations"]], observations)
                self.assertTrue(all(o["mandatory_event"].startswith("DEALLOCATE(") for o in spec["observations"]))
        self.assertEqual(sum(c.meta.evidence == "effect" for c in self.cases.values()), 16)

    def test_exact_files_and_owned_scope(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("final_process_*/*") if p.is_file()}
        self.assertEqual(set(self.outputs), actual)
        self.assertEqual(len(actual), 34)
        for path, content in self.outputs.items():
            self.assertEqual(path.read_bytes(), content)
            self.assertTrue(path.relative_to(ROOT).as_posix().startswith("tests/fixtures/final_process_"))
            if path.suffix == ".f90":
                content.decode("ascii")
                self.assertLessEqual(max(map(len, content.splitlines())), 132)
                self.assertTrue(content.endswith(b"\n"))
        self.assertTrue(all(x["rule"].startswith("S7.5.6.2-") for x in self.specs.values()))

    def test_pending_counts_and_admin_preserving_views(self):
        coverage = {}
        for s in self.specs.values():
            coverage.setdefault(s["rule"], set()).update(s["facets"])
        self.assertEqual(coverage, {r: set(v) for r, v in generated.ELIGIBLE.items()})
        self.assertEqual(sum(map(len, coverage.values())), 17)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 22)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 5)
        for r in self.catalogue["requirements"]:
            self.assertEqual(set(r["pending"]), set(r["facets"]) - coverage[r["id"]])
            self.assertEqual(r["diagnostic_obligation"], "not-required")
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue, self.specs))
        appendix = view.split("## Complete finite pending plans\n", 1)[1].split("## Reproduction and remaining gates", 1)[0]
        self.assertEqual(appendix.count("* **`"), 5)
        for r in self.catalogue["requirements"]:
            for facet, plan in r["pending"].items():
                self.assertIn(f"* **`{facet}`** — {plan}", appendix)
        updated = generated.synced_catalogue(self.catalogue, self.specs)
        self.assertEqual(updated, self.catalogue)
        reviewed = json.loads(json.dumps(updated))
        reviewed["review_state"] = "reviewed"
        reviewed["review_rationale"] = "Synthetic in-memory state test, not an approval."
        r = Registry(ROOT)
        r.catalogues["7.5.6.2"] = reviewed
        reviewed["review_fingerprint"] = r.catalogue_fingerprint("7.5.6.2")
        self.assertEqual(generated.synced_catalogue(reviewed, self.specs), reviewed)
        self.assertIn("Catalogue source review: reviewed.", generated.render_view(reviewed, self.specs))
        reviewed["review_fingerprint"] = "0" * 64
        self.assertIn("Catalogue source review: stale.", generated.render_view(reviewed, self.specs))

    def test_every_observer_rejects_missing_duplicate_wrong_or_unexpected_events(self):
        for name, spec in self.specs.items():
            for obs in spec["observations"]:
                correct = obs["expected"]
                self.assertTrue(generated.model_accepts(correct, obs["before"], correct))
                for i, event in enumerate(correct):
                    with self.subTest(case=name, checkpoint=obs["label"], event=event):
                        self.assertFalse(generated.model_accepts(correct, obs["before"], correct[:i] + correct[i+1:]))
                        self.assertFalse(generated.model_accepts(correct, obs["before"], correct + [event]))
                        wrong_token = list(correct)
                        wrong_token[i] = (event[0], event[1] + 1000)
                        self.assertFalse(generated.model_accepts(correct, obs["before"], wrong_token))
                        wrong_kind = list(correct)
                        wrong_kind[i] = (event[0] + 1000, event[1])
                        self.assertFalse(generated.model_accepts(correct, obs["before"], wrong_kind))
                self.assertFalse(generated.model_accepts(correct, obs["before"], correct + [(9999, 9999)]))

    def test_all_source_permitted_parent_orders_and_only_those_orders_are_accepted(self):
        own = [(10, 1), (20, 11), (20, 13)]
        accepted = []
        for sequence in itertools.permutations(own):
            independently_legal = sequence[0] == (10, 1)
            self.assertEqual(self.accepts(3, "own_before_components", sequence), independently_legal)
            if independently_legal:
                accepted.append(sequence)
        self.assertEqual(len(accepted), 2)
        simple = [(10, 1), (20, 11), (30, 21)]
        for sequence in itertools.permutations(simple):
            self.assertEqual(self.accepts(3, "components_before_parent", sequence), list(sequence) == simple)
        child_pair = [(20, 11), (30, 21)]
        for sequence in itertools.permutations(child_pair):
            self.assertEqual(self.accepts(3, "parent_without_child_final", sequence), list(sequence) == child_pair)
        nodes = [(10, 1), (20, 11), (20, 13), (30, 21), (20, 31), (20, 33), (40, 41)]
        allowed = 0
        for sequence in itertools.permutations(nodes):
            independently_legal = (
                sequence[0] == (10, 1)
                and set(sequence[1:3]) == {(20, 11), (20, 13)}
                and sequence[3] == (30, 21)
                and set(sequence[4:6]) == {(20, 31), (20, 33)}
                and sequence[6] == (40, 41))
            self.assertEqual(self.accepts(3, "recursive_parent", sequence), independently_legal)
            allowed += independently_legal
        self.assertEqual(allowed, 4)
        for sequence in [nodes + [(20, 31), (20, 33)], nodes[:-1], [(40, 41)] + nodes]:
            self.assertFalse(self.accepts(3, "recursive_parent", sequence))

    def test_unordered_siblings_and_event_peers_have_no_declaration_order_oracle(self):
        for group, variant, expected in [
            (2, "siblings", [(20, 11), (20, 13)]),
            (4, "independent_entities", [(20, 17), (20, 19)]),
        ]:
            for sequence in itertools.permutations(expected):
                self.assertTrue(self.accepts(group, variant, sequence))
            self.assertFalse(self.accepts(group, variant, []))
            self.assertFalse(self.accepts(group, variant, [expected[0], expected[0]]))
        self.assertEqual(self.cases[self.name(4, "independent_entities")].meta.evidence, "positive-control")

    def test_component_rank_and_multiplicity_countermodels(self):
        expected = CASES["S7.5.6.2-002"]["array_components"][0]
        self.assertEqual(Counter(expected)[(30, 2)], 2)
        self.assertTrue(self.accepts(2, "array_components", list(reversed(expected))))
        aggregated_scalars = [e for e in expected if e[0] != 20] + [(30, 2), (31, 11), (31, 13)]
        scalarized_arrays = [e for e in expected if e[0] not in [30, 31]] + [
            (20, 21), (20, 23), (20, 25), (20, 27)]
        one_aggregated_array = [e for e in expected if e[0] != 30] + [(30, 4)]
        for incorrect in [aggregated_scalars, scalarized_arrays, one_aggregated_array]:
            self.assertFalse(self.accepts(2, "array_components", incorrect))

    def test_zero_and_no_own_match_controls_are_nonvacuous(self):
        self.assertTrue(self.accepts(1, "array_exact", [(10, 0)], 2))
        self.assertFalse(self.accepts(1, "array_exact", [], 2))
        self.assertTrue(self.accepts(1, "exact_before_elemental", [], 2))
        for sequence in itertools.permutations([(20, 17), (20, 19), (20, 23), (20, 29)]):
            self.assertTrue(self.accepts(1, "exact_before_elemental", sequence, 1))
        self.assertFalse(self.accepts(1, "exact_before_elemental", [(20, 11), (20, 13)], 0))
        self.assertFalse(self.accepts(1, "no_own_match", []))
        self.assertFalse(self.accepts(1, "no_own_match", [(10, 1), (30, 17)]))
        self.assertTrue(self.accepts(2, "empty_outer", [(10, 0)], 0))
        self.assertFalse(self.accepts(2, "empty_outer", [], 0))
        for group, variant in [(1, "array_exact"), (1, "exact_before_elemental"),
                               (1, "assumed_rank"), (2, "empty_outer"), (2, "pointer_exclusion")]:
            spec = self.spec(group, variant)
            traces = [o["expected"] for o in spec["observations"]]
            self.assertTrue(generated.case_accepts(spec["observations"], traces))
            self.assertFalse(generated.case_accepts(spec["observations"], [[] for _ in traces]))
            self.assertFalse(generated.case_accepts(spec["observations"], traces[-1:]))

    def test_full_kind_tuple_and_length_control_countermodels(self):
        observations = self.spec(1, "kind_tuple")["observations"]
        independently_selected = {(1, 1): 101, (1, 2): 102, (2, 1): 201, (2, 2): 202}
        tuples = [(1, 1), (1, 2), (2, 1), (2, 2)]
        for position, kinds in enumerate(tuples):
            correct = observations[position]["expected"]
            self.assertEqual(correct[0][0], independently_selected[kinds])
            for wrong_tuple, wrong_routine in independently_selected.items():
                if wrong_tuple == kinds:
                    continue
                mutated = [(wrong_routine, correct[0][1])] + correct[1:]
                self.assertFalse(self.accepts(1, "kind_tuple", mutated, position))
        self.assertEqual(observations[0]["expected"][0][0], observations[4]["expected"][0][0])
        self.assertNotEqual(observations[0]["expected"][1:], observations[4]["expected"][1:])
        self.assertFalse(self.accepts(1, "kind_tuple", [(101, 13), (901, 7), (902, 9)], 1))
        self.assertFalse(self.accepts(1, "kind_tuple", [(101, 17), (901, 4), (902, 6)], 2))

    def test_emitted_observer_contains_the_checks_exercised_by_countermodels(self):
        required = [
            "if (nlog /= size(kinds)) then\ncall report_actual()\nerror stop 103",
            "count(log_kind(1:nlog)==kinds(i) .and. log_token(1:nlog)==tokens(i))",
            "count(kinds==kinds(i) .and. tokens==tokens(i))) then\ncall report_actual()\nerror stop 104",
            "last_left=i",
            "first_right=min(first_right,i)",
            "if (last_left==0 .or. first_right==nlog+1) then\ncall report_actual()\nerror stop 105",
            "if (last_left>=first_right) then\ncall report_actual()\nerror stop 106",
        ]
        for name, case in self.cases.items():
            source = (case.fixture.root / "source.f90").read_text()
            observer = source.split("module final_types\n", 1)[0]
            with self.subTest(case=name):
                self.assertEqual(observer, generated.LOG_MODULE)
                for check in required:
                    self.assertIn(check, observer)
                self.assertNotIn("type(", observer.lower())

    def test_pointer_exclusion_requires_owner_and_independent_target_events(self):
        spec = self.spec(2, "pointer_exclusion")
        self.assertFalse(self.accepts(2, "pointer_exclusion", [], 0))
        self.assertFalse(self.accepts(2, "pointer_exclusion", [(10, 11), (20, 31)], 0))
        self.assertFalse(self.accepts(2, "pointer_exclusion", [], 1))
        self.assertTrue(generated.case_accepts(spec["observations"], [[(10, 11)], [(20, 31)]]))
        source = self.source(2, "pointer_exclusion")
        self.assertIn("type(leaf), allocatable, target :: target", source)
        self.assertIn("owner%link=>target", source)
        self.assertNotIn("deallocate(owner%link", source)
        body = source.split("program p\n", 1)[1]
        self.assertNotIn("owner%", body.split("deallocate(owner,stat=status)", 1)[1])
        self.assertLess(body.index("deallocate(owner"), body.index("deallocate(target"))

    def test_all_finalizers_and_setup_have_valid_roles_and_lifetimes(self):
        for name, case in self.cases.items():
            source = (case.fixture.root / "source.f90").read_text()
            main = source.split("program p\n", 1)[1]
            callbacks = re.findall(r"(?im)^(?:impure elemental )?subroutine (finish_\w+)\(self\)", source)
            self.assertTrue(callbacks)
            for callback_name in callbacks:
                self.assertNotRegex(main, rf"(?i)call\s+{callback_name}\b")
            self.assertNotIn("call record_event", main)
            self.assertNotRegex(source, r"(?i)class\s*\([^)]*\).*::\s*self")
            self.assertNotRegex(source, r"(?i)intent\s*\(\s*out\s*\).*::\s*self")
            self.assertNotRegex(source, r"(?i)\bvalue\s*::\s*self")
            self.assertNotIn("pure subroutine", source)
            for variable in self.specs[name]["finalizable_variables"]:
                self.assertNotRegex(main, rf"(?im)^\s*{variable}(?:\([^)]*\))?\s*=(?!=|>)")
                self.assertIn(f"allocated({variable})", main)
                self.assertIn(f"allocate({variable}", main)
            self.assertEqual(main.count("call expect_log("), len(self.specs[name]["observations"]))
            position = 0
            for observation in self.specs[name]["observations"]:
                start = main.index(observation["mandatory_event"].lower().replace(")", ",stat=status)"), position)
                check = main.index("call expect_log(", start)
                self.assertIn("if (status/=0) error stop 114", main[start:check])
                position = check + 1
            self.assertIn("integer, save :: nlog=0", source)
            self.assertNotIn("error stop", source.split("program p\n", 1)[0].split("module final_types\n", 1)[1]
                             if "assumed_rank" not in name else "")

    def test_signature_families_are_not_illegal_selection_models(self):
        source = self.source(1, "kind_tuple")
        for ka, kb in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            self.assertIn(f"type(item(ka={ka},kb={kb},n=*,m=*)), intent(inout) :: self", source)
        self.assertNotRegex(source, r"(?i)integer\s*\(\s*(?:ka|kb)\s*\)")
        source = self.source(1, "assumed_rank")
        definitions = source.split("module final_types\n", 1)[1].split("\ncontains\nsubroutine", 1)[0]
        self.assertEqual(re.findall(r"(?im)^final :: (.*)$", definitions), ["finish_any"])
        self.assertIn("select rank(self)", source)
        source = self.source(1, "exact_before_elemental")
        self.assertIn("impure elemental subroutine finish_each(self)", source)
        self.assertIn("type(item), intent(inout) :: self(:)", source)
        self.assertNotIn("self(..)", source)
        for case in self.cases.values():
            source = (case.fixture.root / "source.f90").read_text()
            self.assertTrue(all("," not in line for line in re.findall(r"(?im)^final :: (.*)$", source)))
        self.assertIn("use final_types, only: item", self.source(1, "private_name"))
        self.assertIn("private :: finish_scalar", self.source(1, "private_name"))

    def test_shared_parameter_corpus_is_byte_exact(self):
        corpus = parameters.build_corpus()
        self.assertEqual((len(corpus.cases), len(corpus.files)), (66, 105))
        self.assertFalse(set(corpus.files) & set(self.outputs))
        for path, expected in corpus.files.items():
            self.assertEqual(path.read_bytes(), expected)


if __name__ == "__main__":
    unittest.main()
