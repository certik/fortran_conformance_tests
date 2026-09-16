import importlib.util
import itertools
import json
from pathlib import Path
import re
import tempfile
import unittest

import run_tests as runner


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "component_initialization_generator", ROOT / "tools/generate_component_initialization_fixtures.py")
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class ComponentInitializationFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = GENERATOR.build_corpus()
        cls.registry = runner.Registry()
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.all_cases = all_cases
        cls.cases = {case.name: case for case in all_cases if case.name in cls.corpus.cases}

    def body(self, name, filename="source.f90"):
        case = self.cases[name]
        return (case.fixture.root / filename).read_text() if case.fixture else Path(case.path).read_text()

    def test_exact_case_set_phases_and_evidence(self):
        self.assertEqual(set(self.cases), set(self.corpus.cases))
        self.assertEqual(len(self.cases), 156)
        self.assertEqual(sum(case.kind == "invalid" for case in self.cases.values()), 33)
        self.assertEqual(sum(item["phase"] == "run" for item in self.corpus.cases.values()), 63)
        self.assertEqual(len(self.corpus.repairs), 33)
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assertEqual(case.rule, self.corpus.cases[name]["rule"])
                self.assertEqual(case.meta.facets, self.corpus.cases[name]["facets"])
                self.assertEqual(case.meta.standard, "f2023")
                self.assertEqual(case.meta.profiles, [])
                if case.rule == "S7.5.4.8-002":
                    self.assertEqual(case.meta.evidence, "positive-control")
                if case.kind == "invalid":
                    self.assertEqual(case.fixture.expectation.phase, "compile")
                    self.assertEqual(case.fixture.expectation.outcome, "diagnose")

    def test_generated_files_match_exact_bytes(self):
        for path, raw in self.corpus.files.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), raw)
                if path.suffix == ".f90":
                    self.assertLessEqual(max(map(len, raw.splitlines())), 132)

    def test_prior_parameter_generator_inputs_are_unchanged(self):
        old = GENERATOR.BASE.build_corpus()
        self.assertEqual(len(old.cases), 66)
        for path, raw in old.files.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), raw)

    def test_shared_corpus_namespace_root_and_optional_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            c = GENERATOR.BASE.Corpus(namespace="probe", root=root)
            c.compile("C770", "coarray", ["target"], "end\n", requires=("coarray",))
            name = "C770_valid__probe_coarray"
            self.assertIn(name, c.cases)
            manifest = json.loads(c.files[root / c.cases[name]["path"]])
            self.assertEqual(manifest["requires"], ["coarray"])
            c.run("S7.5.4.8-002", "probe", ["owner"], "end\n",
                  evidence="positive-control", requires=("coarray",))
            raw = c.files[root / c.cases["S7_5_4_8_002_valid__probe"]["path"]]
            self.assertIn(b"! evidence: positive-control\n", raw)
            self.assertIn(b"! requires: coarray\n", raw)
            self.assertTrue(all(path.is_relative_to(root) for path in c.files))

    def test_pending_partition_and_nonexecuted_classifications(self):
        covered = self.corpus.coverage()
        linked = self.registry.evidence.validate_cases(self.all_cases)
        pending = direct = linked_count = 0
        for section in GENERATOR.SECTIONS:
            for requirement in self.registry.catalogues[section]["requirements"]:
                actual = covered.get(requirement["id"], set())
                linked_facets = set(linked.get(requirement["id"], {}))
                self.assertEqual(set(requirement["pending"]),
                                 set(requirement["facets"]) - actual - linked_facets)
                pending += len(requirement["pending"])
                direct += len(actual)
                linked_count += len(linked_facets)
        self.assertEqual((direct, pending + linked_count), (113, 35))
        for rule in ("S7.5.4.6-002", "S7.5.4.6-011"):
            self.assertNotIn(rule, covered)
        self.assertIn("inherited-original-default-graph",
                      self.registry.requirements["S7.5.4.8-001"]["pending"])
        self.assertIn("component-name-use-graph",
                      self.registry.requirements["S7.5.4.8-002"]["pending"])

    def test_all_negatives_have_exact_source_repairs(self):
        self.assertEqual({r["invalid"] for r in self.corpus.repairs},
                         {name for name, case in self.cases.items() if case.kind == "invalid"})
        for repair in self.corpus.repairs:
            with self.subTest(case=repair["invalid"]):
                bad = self.body(repair["invalid"], repair["file"])
                good = self.body(repair["valid"], repair["file"])
                self.assertEqual(bad.count(repair["wrong"]), 1)
                self.assertEqual(bad.replace(repair["wrong"], repair["repaired"], 1), good)
                bad_case, good_case = self.cases[repair["invalid"]], self.cases[repair["valid"]]
                for filename in bad_case.fixture.files:
                    if filename != repair["file"]:
                        self.assertEqual((bad_case.fixture.root / filename).read_bytes(),
                                         (good_case.fixture.root / filename).read_bytes())

    def test_diagnostics_require_the_right_message_file_and_point(self):
        for case in self.cases.values():
            if case.kind != "invalid":
                continue
            expected = case.fixture.expectation.diagnostic
            for family in ("lfortran", "gfortran", "flang"):
                comp = runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023")
                for status in (0, 1):
                    for filename, line, message, outcome in (
                        (expected["file"], expected["line"], expected["contains_any"][0], "pass"),
                        ("other.f90", expected["line"], expected["contains_any"][0], "fail"),
                        (expected["file"], 1, expected["contains_any"][0], "fail"),
                        (expected["file"], expected["line"], "Unclassifiable statement", "fail"),
                        (expected["file"], expected["line"], "Symbol 'unrelated' is not declared", "fail"),
                        (expected["file"], expected["line"],
                         "Not implemented: " + expected["contains_any"][0], "fail"),
                    ):
                        with self.subTest(case=case.name, family=family, status=status,
                                          file=filename, line=line, message=message):
                            point = f"{line}-{line}:1-20" if family == "lfortran" else f"{line}:1"
                            severity = "semantic error" if family == "lfortran" else "Error"
                            text = f"{filename}:{point}: {severity}: {message}\n"
                            result = runner.judge_diagnostic(
                                runner.ProcessResult(status, text), comp, case.rule, expected)
                            self.assertEqual(result.outcome, outcome)

    def test_wrong_facility_and_selector_causes_do_not_pass(self):
        def outcome(name, message):
            case = self.cases[name]
            expected = case.fixture.expectation.diagnostic
            text = f"{expected['file']}:{expected['line']}:1: Error: {message}"
            return runner.judge_diagnostic(
                runner.ProcessResult(1, text), runner.Compiler("gfortran", "gfortran", "f2023"),
                case.rule, expected).outcome
        blanket = ("The component 'value' at (1) of derived type 'record' has paramterized type "
                   "or array length parameters, which is not compatible with a default initializer")
        for variant in ("length", "lower", "upper"):
            self.assertEqual(outcome("C767_invalid__initialization_" + variant, blanket), "fail")
            self.assertEqual(outcome("C767_invalid__initialization_" + variant,
                             "Component 'value' at (1) with KIND or LEN parameter must not have default initialization"),
                             "fail")
        for name, case in self.cases.items():
            if case.kind == "invalid" and case.rule in ("C769", "C770"):
                self.assertEqual(outcome(name,
                    "Initialization of `alias` must reduce to a compile time constant."), "fail")
        generic = "An initial data target must be a designator with constant subscripts"
        for variant in ("coindexed", "vector", "substring_lower", "substring_upper",
                        "no_save", "no_target", "allocatable"):
            self.assertEqual(outcome("C770_invalid__initialization_" + variant, generic), "fail")
        for variant in ("element_variable", "lower_variable", "upper_variable", "stride_variable"):
            self.assertEqual(outcome("C770_invalid__initialization_" + variant, generic), "pass")
        self.assertEqual(outcome("R745_invalid__initialization_private_list",
                                 "Unexpected attribute declaration statement at (1)"), "fail")

    def test_event_witnesses_count_verifications_and_do_not_reset_themselves(self):
        for kind in ("null_data", "null_procedure", "data", "procedure", "value"):
            for event in ("initial", "local", "intent_out", "block", "allocate", "allocate_pointer"):
                text = GENERATOR.event_program(kind, event)
                self.assertIn("integer :: checks_completed=0", text)
                self.assertIn("checks_completed=checks_completed+1", text)
                self.assertIn(f"if (checks_completed /= {1 if event == 'initial' else 2})", text)
                reset = text.split("subroutine reset(item)\n", 1)[1].split("end subroutine", 1)[0]
                self.assertEqual(reset, "type(record), intent(out) :: item\ncall verify(item)\n")
                if event.startswith("allocate"):
                    self.assertLess(text.index("if (stat /= 0) error stop 10"), text.index("call verify(item)", text.index("program event_witness")))
                    self.assertNotIn("source=", text.lower())
        nulls = GENERATOR.event_types("null_data") + GENERATOR.event_types("null_procedure")
        self.assertNotIn("mold", nulls.lower())
        self.assertEqual(nulls.count("=> null()"), 2)

    def test_missing_save_and_selector_cases_keep_other_premises(self):
        bad = self.body("C770_invalid__initialization_no_save")
        good = self.body("C770_valid__initialization_no_save_repair")
        self.assertIn("subroutine local_definition", bad)
        self.assertIn("integer, target :: target\n", bad)
        self.assertNotIn("module", bad)
        self.assertNotIn("target =", bad)
        self.assertIn("integer, target, save :: target\n", good)
        for variant in ("substring_lower", "substring_upper"):
            self.assertIn("character(:), pointer", self.body("C770_invalid__initialization_" + variant))
        strided = self.body("C769_invalid__initialization_strided")
        self.assertIn("contiguous :: alias(:) => values(1:4:2)", strided)

    def test_order_consumers_and_descendant_builds_keep_their_contexts(self):
        keyword = self.body("S7_5_4_7_002_valid__initialization_parent_keyword")
        self.assertIn("child(parent=parent(2,3),middle=5)", keyword)
        for scope in ("001", "002"):
            for direction in ("input", "output"):
                text = self.body(f"S7_5_4_7_{scope}_valid__initialization_formatted_{direction}")
                self.assertIn("iostat=stat", text)
                self.assertIn("if (stat /= 0)", text)
                self.assertNotIn("pointer", text.lower())
                self.assertNotIn("allocatable", text.lower())
        grandchild = self.cases["S7_5_4_8_002_valid__initialization_grandchild"]
        self.assertEqual([step.source for step in grandchild.fixture.build],
                         ["parent.f90", "child.f90", "grandchild.f90", "main.f90"])
        for variant in ("default", "explicit"):
            bad = self.cases[f"C7107_invalid__initialization_{variant}_private"]
            self.assertEqual(bad.rule, "C7107")
            self.assertEqual(bad.fixture.expectation.diagnostic["file"], "main.f90")
            self.assertEqual(bad.fixture.expectation.step, "main")

    def test_formatted_output_setup_is_independent_of_component_order(self):
        names = ("zed", "alpha", "middle")
        for scope in ("001", "002"):
            with self.subTest(scope=scope):
                text = self.body(f"S7_5_4_7_{scope}_valid__initialization_formatted_output")
                setup = text[:text.index("write(")]
                assignments = re.findall(r"(?m)^item%(zed|alpha|middle)=(\d+)$", setup)
                self.assertEqual(assignments, [("zed", "2"), ("alpha", "3"), ("middle", "5")])
                self.assertNotRegex(setup, r"\bitem\s*=\s*(?:record|child)\s*\(")
                expected = re.search(r"if \(text /= '([^']+)'\)", text).group(1)
                values = dict(assignments)
                for order in itertools.permutations(names):
                    actual = " ".join(values[name] for name in order)
                    self.assertEqual(actual == expected, order == names)


if __name__ == "__main__":
    unittest.main()
