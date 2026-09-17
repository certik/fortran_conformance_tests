"""Independent literal, DATA OBJECT/rank, source-state and actual-guard regressions."""
from collections import Counter
import copy
import re
from pathlib import Path
import sys
import unittest

import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_array_constructor_value_fixtures as generated
import generate_derived_parameter_fixtures as parameters

CASES = {
    "sequence": ("S7.8-001", ["rank-one-and-scalar-sequence", "higher-rank-flattening"]),
    "ordinary_loops": ("S7.8-008", ["default-increment-sequence", "positive-and-negative-strides", "multiple-body-values"]),
    "dependent_bodies": ("S7.8-008", ["nested-dependent-bounds", "array-valued-body-sequence"]),
    "integer_empty": ("S7.8-009", ["typed-empty-and-zero-trip", "zero-sized-array-ac-value"]),
    "character_empty": ("S7.8-009", ["empty-character-parameters"]),
}
EXPECTED = {
    "sequence": {"scalars": [11,13,17], "matrix": [5,11,13,17,19,23]},
    "ordinary_loops": {"default_step": [1,2,3], "positive_step": [1,3,5],
                       "negative_step": [5,3,1], "multiple_body": [1,10,2,20]},
    "dependent_bodies": {"nested": [11,21,22,31,32,33], "array_body": [32,38,33,39]},
    "integer_empty": {"integer_control": [7], "typed_empty": [], "zero_trip": [], "empty_source": [11,13]},
    "character_empty": {"character_control": ["abc"], "character_fixed": [], "character_runtime": []},
}
EXPRESSIONS = {
    "scalars": "[11,13,17]", "matrix": "[5,m,23]",
    "default_step": "[(i,i=1,3)]", "positive_step": "[(i,i=1,5,2)]",
    "negative_step": "[(i,i=5,1,-2)]", "multiple_body": "[(i,10*i,i=1,2)]",
    "nested": "[((10*i+j,j=1,i),i=1,3)]",
    "array_body": "[(vector+i,i=1,2)]",
    "integer_control": "[7]", "typed_empty": "[integer ::]",
    "zero_trip": "[(i,i=1,0)]", "empty_source": "[11,empty,13]",
    "character_control": "[character(len=3) :: 'abc']",
    "character_fixed": "[character(len=3) ::]",
    "character_runtime": "[character(len=n) ::]",
}
SETUP = {
    "sequence": ["m(1,1)=11", "m(2,1)=13", "m(1,2)=17", "m(2,2)=19"],
    "ordinary_loops": [],
    "dependent_bodies": ["vector(1)=31", "vector(2)=37"],
    "integer_empty": [],
    "character_empty": ["n=3"],
}
DECLARATIONS = {
    "sequence": ["integer :: m(2,2)"], "ordinary_loops": ["integer :: i"],
    "dependent_bodies": ["integer :: vector(2)", "integer :: i,j"],
    "integer_empty": ["integer :: empty(0)", "integer :: i"],
    "character_empty": ["integer :: n"],
}
COUNTS = {"sequence": 15, "ordinary_loops": 25, "dependent_bodies": 16,
          "integer_empty": 15, "character_empty": 16}


def do_values(initial, terminal, increment=1):
    if any(type(x) is not int for x in (initial, terminal, increment)) or increment == 0:
        raise ValueError("ordinary finite INTEGER controls with nonzero step required")
    values = []
    value = initial
    while value <= terminal if increment > 0 else value >= terminal:
        values.append(value)
        value += increment
    return values


class ArrayConstructorValueFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if "/fixtures/array_constructor_value_" in case.path}
        cls.catalogue = cls.registry.catalogues["7.8"]

    def name(self, variant):
        return generated.identifier(CASES[variant][0], variant)

    def spec(self, variant):
        return self.specs[self.name(variant)]

    def source(self, variant):
        return (self.cases[self.name(variant)].fixture.root / "source.f90").read_text()

    def test_exact_five_program_partition_and_only_ten_facets(self):
        names = {self.name(variant) for variant in CASES}
        self.assertEqual(set(self.specs), names)
        self.assertEqual(set(self.cases), names)
        self.assertEqual(len(names), 5)
        self.assertEqual(sum(len(s["facets"]) for s in self.specs.values()), 10)
        self.assertEqual(sum(s["expected_check_count"] for s in self.specs.values()), 87)
        for variant, (rule, facets) in CASES.items():
            spec, case = self.spec(variant), self.cases[self.name(variant)]
            self.assertEqual(case.rule, rule)
            self.assertEqual(spec["facets"], facets)
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.meta.evidence, "effect")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.exit_code, 0)
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)
            self.assertEqual(spec["expected_check_count"], COUNTS[variant])
            self.assertEqual({op["name"]: op["expected"] for op in spec["operations"]}, EXPECTED[variant])
            for op in spec["operations"]:
                self.assertEqual(op["expression"], EXPRESSIONS[op["name"]])

    def test_exact_files_and_no_other_owned_input_surfaces(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("array_constructor_value_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 10)
        for path, content in self.files.items():
            self.assertEqual(path.read_bytes(), content)
            content.decode("ascii")
            self.assertTrue(content.endswith(b"\n"))
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, content.splitlines())), 132)

    def verify_source(self, variant, source):
        spec = self.spec(variant)
        self.assertTrue(source.startswith(generated.CHECKS))
        main, observers = source.split("program p\n", 1)[1].split("contains\n", 1)
        declarations = re.findall(r"(?m)^integer :: .+$", main)
        self.assertEqual(declarations, DECLARATIONS[variant])
        assignments = re.findall(r"(?m)^[a-z]\w*(?:\([^)]*\))?=[^\n]+$", main)
        self.assertEqual(assignments, SETUP[variant])
        self.assertEqual(spec["setup"], SETUP[variant])
        self.assertEqual(spec["declarations"], DECLARATIONS[variant])
        if assignments:
            self.assertLess(max(main.index(line) for line in assignments), main.index("call check_integer"))
        expected_main = [
            "use array_value_checks, only: check_integer, check_logical, finish_checks",
            "implicit none",
        ] + DECLARATIONS[variant] + SETUP[variant]
        self.assertNotIn("rank(", main)
        self.assertNotRegex(source, r"(?i)\brank\s*\(\s*\[")
        for op in spec["operations"]:
            name, expression = op["name"], EXPRESSIONS[op["name"]]
            expected = EXPECTED[variant][name]
            expected_main.append(f"call check_integer('{name}:size',size({expression}),{len(expected)})")
            match = re.search(rf"(?ms)^subroutine observe_{name}\(a\)\n(.*?)^end subroutine observe_{name}$", observers)
            self.assertIsNotNone(match)
            body = match[1]
            dtype = "character(len=*)" if variant == "character_empty" else "integer"
            expected_body = [
                f"{dtype}, intent(in) :: a(..)",
                f"call check_integer('{name}:rank',rank(a),1)",
                "select rank(a)",
                "rank(1)",
            ]
            size_guard = f"call check_integer('{name}:argument-size',size(a),{len(expected)})"
            expected_body.append(size_guard)
            self.assertIn(size_guard, body)
            if variant == "character_empty":
                self.assertEqual(op["expected_length"], 3)
                expected_main.append(f"call check_integer('{name}:length',len({expression}),3)")
                expected_body.append(f"call check_integer('{name}:argument-length',len(a),3)")
            expected_main.append(f"call observe_{name}({expression})")
            for index, value in enumerate(expected, 1):
                if type(value) is int:
                    check = f"call check_integer('{name}:value-{index}',a({index}),{value})"
                else:
                    check = f"call check_logical('{name}:value-{index}',a({index})=='{value}',.true.)"
                expected_body.append(check)
                self.assertIn(check, body)
                self.assertLess(body.index(size_guard), body.index(check))
            expected_body += [
                "rank default",
                f"print *, 'UNEXPECTED_RANK','{name}',rank(a)",
                "error stop 4",
                "end select",
            ]
            self.assertEqual(body, "\n".join(expected_body) + "\n")
            if not expected:
                self.assertNotRegex(body, r"\ba\(\d+\)")
            self.assertNotRegex(body, r"(?im)^\s*do\b")
            self.assertLess(body.index("rank(a)"), body.index("select rank(a)"))
            self.assertLess(body.index("rank(1)"), body.index(size_guard))
            self.assertLess(body.index(size_guard), body.index("rank default"))
            self.assertNotRegex(body, r"\b(?:pointer|allocatable|codimension|value)\s*(?:::|,)")
        self.assertEqual(main.count("call finish_checks("), 1)
        self.assertIn(f"call finish_checks({COUNTS[variant]})", main)
        expected_main.append(f"call finish_checks({COUNTS[variant]})")
        self.assertEqual(main, "\n".join(expected_main) + "\n")
        self.assertNotRegex(source.lower(), r"\b(?:reshape|pack|transfer|kind|storage_size|c_sizeof|allocated|associated)\s*\(")
        self.assertNotRegex(source.lower(), r"\b(?:real|complex|class|pointer|allocatable|concurrent|iso_c_binding)\b")
        self.assertNotRegex(source, r"(?i)\b[bzo]['\"]")
        self.assertNotRegex(main, r"(?im)^character")
        self.assertNotIn("expected=[", source.replace(" ", ""))

    def test_data_object_rank_rejects_direct_constructor_and_fixed_rank_proxies(self):
        count = 0
        for variant in CASES:
            source = self.source(variant)
            self.verify_source(variant, source)
            for op in self.spec(variant)["operations"]:
                original = f"call check_integer('{op['name']}:rank',rank(a),1)"
                bad = original.replace("rank(a)", f"rank({op['expression']})")
                with self.assertRaises(AssertionError):
                    self.verify_source(variant, source.replace(original, bad))
                count += 1
            dtype = "character(len=*)" if variant == "character_empty" else "integer"
            for proxy in (
                source.replace(f"{dtype}, intent(in) :: a(..)", f"{dtype}, intent(in) :: a(:)"),
                source.replace("rank(a),1)", "1,1)"),
                source.replace("rank default\n", ""),
            ):
                with self.assertRaises(AssertionError):
                    self.verify_source(variant, proxy)
            spec = self.spec(variant)
            observed = {g["label"]: g["expected"] for g in spec["observations"]}
            for g in spec["observations"]:
                if g["family"] == "assumed-rank-argument":
                    self.assertEqual(g["expression"], "rank(a)")
                    self.assertNotEqual(g["location"], "main")
                    for wrong_rank in (0, 2):
                        self.assertFalse(generated.accepts(
                            spec["observations"], dict(observed, **{g["label"]: wrong_rank})))
        self.assertEqual(count, 15)
        source = self.source("sequence")
        fixed_destination = source.replace("integer :: m(2,2)", "integer :: m(2,2),rank_proxy(1)")
        fixed_destination = fixed_destination.replace("rank(a),1)", "rank(rank_proxy),1)")
        with self.assertRaises(AssertionError):
            self.verify_source("sequence", fixed_destination)

    def test_inferred_control_names_supply_types_without_host_value_reads(self):
        for variant, declaration in (
            ("ordinary_loops", "integer :: i"),
            ("dependent_bodies", "integer :: i,j"),
            ("integer_empty", "integer :: i"),
        ):
            source = self.source(variant)
            self.assertIn(declaration + "\n", source)
            self.assertNotIn("integer::", source)
            self.assertNotRegex(source, r"(?m)^[ij]\s*=")
            with self.assertRaises(AssertionError):
                self.verify_source(variant, source.replace(declaration + "\n", ""))
            completion = f"call finish_checks({COUNTS[variant]})"
            host_read = source.replace(completion, "call check_integer('host-after',i,3)\n" + completion)
            with self.assertRaises(AssertionError):
                self.verify_source(variant, host_read)
        source = self.source("dependent_bodies")
        with self.assertRaises(AssertionError):
            self.verify_source("dependent_bodies", source.replace("j=1,i", "j=1,j"))

    def test_observer_actual_argument_spans_bind_unconstrained_rank_probes(self):
        total = 0
        for variant in CASES:
            spec, source = self.spec(variant), self.source(variant)
            lines = source.splitlines()
            self.assertEqual(len(spec["argument_bindings"]), len(spec["operations"]))
            for item in spec["argument_bindings"]:
                line = lines[item["line"] - 1]
                first, last = item["first_column"] - 1, item["last_column"]
                self.assertEqual(line, item["source_text"])
                self.assertEqual(line[first:last], EXPRESSIONS[item["operation"]])
                self.assertEqual(line, f"call observe_{item['operation']}({item['expression']})")
                self.assertEqual(item["category"], "character" if variant == "character_empty" else "integer")
                self.assertEqual(line[:first], f"call observe_{item['operation']}(")
                self.assertEqual(line[last:], ")")
                total += 1
        self.assertEqual(total, 15)

    def test_actual_sources_use_direct_inquiries_named_setup_and_literal_element_guards(self):
        for variant in CASES:
            with self.subTest(case=variant):
                self.verify_source(variant, self.source(variant))

    def test_matrix_column_order_is_independent_of_setup_and_expected_arrays(self):
        matrix = {(1,1):11, (2,1):13, (1,2):17, (2,2):19}
        column_order = [matrix[(i,j)] for j in (1,2) for i in (1,2)]
        row_order = [matrix[(i,j)] for i in (1,2) for j in (1,2)]
        expected = [5,11,13,17,19,23]
        self.assertEqual([5] + column_order + [23], expected)
        self.assertNotEqual([5] + row_order + [23], expected)
        self.assertNotEqual(column_order, row_order)
        source = self.source("sequence")
        for mutation in (
            source.replace("m(2,1)=13", "m(2,1)=17"),
            source.replace("m(1,2)=17", "m(1,2)=13"),
            source.replace("m(1,1)=11", "m=reshape([11,13,17,19],[2,2])"),
        ):
            with self.assertRaises(AssertionError):
                self.verify_source("sequence", mutation)

    def test_ordinary_DO_default_positive_negative_and_multiple_body_models(self):
        self.assertEqual(do_values(1,3), [1,2,3])
        self.assertEqual(do_values(1,5,2), [1,3,5])
        self.assertEqual(do_values(5,1,-2), [5,3,1])
        self.assertEqual(do_values(1,0), [])
        self.assertEqual([v for i in do_values(1,2) for v in (i,10*i)], [1,10,2,20])
        self.assertNotEqual([1,2,10,20], EXPECTED["ordinary_loops"]["multiple_body"])
        self.assertNotEqual([1,3], EXPECTED["ordinary_loops"]["positive_step"])
        self.assertNotEqual([1,3,5], EXPECTED["ordinary_loops"]["negative_step"])
        with self.assertRaises(ValueError):
            do_values(1,3,0)
        controls = [control for op in self.spec("ordinary_loops")["operations"] for control in op["controls"]]
        self.assertTrue(all(type(c["initial"]) is int and type(c["terminal"]) is int and c["increment"] != 0 for c in controls))
        self.assertEqual([c["explicit_step"] for c in controls], [False,True,True,False])

    def test_nested_bounds_and_array_bodies_use_defined_outer_and_named_vector_values(self):
        values = []
        for outer in do_values(1,3):
            self.assertIn(outer, (1,2,3))
            for inner in do_values(1,outer):
                values.append(10*outer+inner)
        self.assertEqual(values, [11,21,22,31,32,33])
        vector = {1:31,2:37}
        array_body = [vector[position]+i for i in do_values(1,2) for position in (1,2)]
        self.assertEqual(array_body, [32,38,33,39])
        self.assertNotEqual([32,33,38,39], array_body)
        nested = self.spec("dependent_bodies")["operations"][0]
        self.assertEqual(nested["controls"][1]["variable"], "j")
        self.assertEqual(nested["controls"][1]["defined_outer_dependency"], "i")
        self.assertEqual(nested["controls"][1]["terminal"], "i")
        source = self.source("dependent_bodies")
        self.assertIn("j=1,i", source)
        self.assertNotIn("j=1,j", source)
        self.assertIn("integer :: i,j\n", source)

    def test_empty_integer_has_real_empty_input_and_nonempty_controls_without_empty_loops(self):
        spec = self.spec("integer_empty")
        self.assertEqual(spec["declarations"], ["integer :: empty(0)", "integer :: i"])
        self.assertEqual(spec["setup"], [])
        self.assertEqual(EXPECTED["integer_empty"], {
            "integer_control":[7], "typed_empty":[], "zero_trip":[], "empty_source":[11,13]})
        source = self.source("integer_empty")
        self.assertIn("call check_integer('typed_empty:rank',rank(a),1)", source)
        self.assertIn("size([(i,i=1,0)])", source)
        self.assertIn("a(1),11)", source)
        self.assertIn("a(2),13)", source)
        self.assertNotRegex(source, r"(?im)^\s*do\b")
        self.assertNotIn("empty=", source)
        self.assertNotIn("allocate", source.lower())

    def test_empty_character_length_is_observed_before_any_fixed_destination(self):
        source = self.source("character_empty")
        main = source.split("program p\n",1)[1].split("contains\n",1)[0]
        self.assertIn("integer :: n\nn=3\n", main)
        self.assertNotIn("parameter", main.lower())
        self.assertIn("len([character(len=3) ::])", main)
        self.assertIn("len([character(len=n) ::])", main)
        self.assertEqual(source.count("character(len=*), intent(in) :: a(..)"), 3)
        self.assertNotIn("character(len=3), intent", source)
        self.assertNotRegex(source, r"\b[ij]=1,0\b")
        self.assertIn("a(1)=='abc'", source)
        self.assertIn("size([character(len=3) :: 'abc'])", main)

    def test_every_literal_guard_rejects_missing_extra_wrong_and_type_confused_observations(self):
        for spec in self.specs.values():
            correct = {g["label"]:g["expected"] for g in spec["observations"]}
            self.assertTrue(generated.accepts(spec["observations"], correct))
            self.assertFalse(generated.accepts(spec["observations"], {}))
            self.assertFalse(generated.accepts(spec["observations"], dict(correct, phantom=1)))
            for label, expected in correct.items():
                missing = dict(correct)
                del missing[label]
                self.assertFalse(generated.accepts(spec["observations"], missing))
                wrong = not expected if type(expected) is bool else expected+1
                self.assertFalse(generated.accepts(spec["observations"], dict(correct, **{label:wrong})))
                wrong_type = int(expected) if type(expected) is bool else True
                self.assertFalse(generated.accepts(spec["observations"], dict(correct, **{label:wrong_type})))

    def test_actual_primitive_guards_and_single_span_sensitivity_bindings(self):
        total = 0
        for variant in CASES:
            spec, source = self.spec(variant), self.source(variant)
            lines = source.splitlines()
            self.assertEqual(len(spec["guard_bindings"]), COUNTS[variant]+1)
            families = {g["family"] for g in spec["guard_bindings"]}
            self.assertEqual(families, set(spec["sensitivity_representatives"]))
            for g in spec["guard_bindings"]:
                line = lines[g["line"]-1]
                self.assertEqual(line, g["source_text"])
                first, last = g["first_column"]-1, g["last_column"]
                self.assertEqual(line[first:last], g["expected_text"])
                wrong = generated.literal(not g["expected"] if type(g["expected"]) is bool else g["expected"]+1)
                altered = line[:first]+wrong+line[last:]
                self.assertEqual(altered[:first], line[:first])
                self.assertTrue(altered.endswith(line[last:]))
                self.assertNotEqual(altered, line)
                total += 1
            self.assertIn("if (actual/=expected) then", source)
            self.assertIn("if (actual .neqv. expected) then", source)
            self.assertIn("if (checked/=expected) then", source)
            self.assertIn("integer, save :: checked=0", source)
        self.assertEqual(total, 92)

    def test_source_mutations_cannot_hide_data_object_rank_length_or_index_guards(self):
        source = self.source("sequence")
        for altered in (
            source.replace("rank(a)", "1"),
            source.replace("a(2),13)", "a(2),17)"),
            source.replace("call finish_checks(15)", "call finish_checks(0)"),
        ):
            with self.assertRaises(AssertionError):
                self.verify_source("sequence", altered)
        source = self.source("character_empty")
        for altered in (
            source.replace("n=3\n", ""),
            source.replace("len([character(len=n) ::])", "3"),
            source.replace("character(len=*), intent(in)", "character(len=3), intent(in)"),
        ):
            with self.assertRaises(AssertionError):
                self.verify_source("character_empty", altered)

    def test_source_admin_is_preserved_and_all_97_unselected_plans_stay_pending(self):
        self.assertEqual(len(self.catalogue["requirements"]), 26)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 107)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 97)
        for requirement in self.catalogue["requirements"]:
            covered = set(generated.ELIGIBLE.get(requirement["id"], []))
            self.assertEqual(set(requirement["pending"]), set(requirement["facets"])-covered)
        r = next(r for r in self.catalogue["requirements"] if r["id"]=="S7.8-001")
        self.assertIn("mixed-shapes-and-empty-source", r["pending"])
        admin = {k:v for k,v in self.catalogue.items() if k.startswith("review_")}
        self.assertEqual({k:v for k,v in generated.synced_catalogue(self.catalogue,self.specs).items()
                          if k.startswith("review_")}, admin)
        self.assertEqual(generated.synced_catalogue(self.catalogue,self.specs), self.catalogue)
        view = (ROOT/generated.VIEW).read_text()
        self.assertEqual(view,generated.render_view(self.catalogue,self.specs))
        native = Registry(ROOT)
        native.catalogues = {"7.8":self.catalogue}
        native.render()
        appendix = view.split("## Complete finite pending plans\n",1)[1].split("## Reproduction and remaining gates",1)[0]
        self.assertEqual(appendix.count("* **`"),97)
        for r in self.catalogue["requirements"]:
            for facet,plan in r["pending"].items():
                self.assertIn(f"* **`{facet}`** - {plan}",appendix)
        reviewed = copy.deepcopy(self.catalogue)
        reviewed.update(review_state="reviewed",review_rationale="Synthetic in-memory state; no approval is written.")
        native = Registry(ROOT)
        native.catalogues["7.8"] = reviewed
        reviewed["review_fingerprint"] = native.catalogue_fingerprint("7.8")
        self.assertEqual(generated.synced_catalogue(reviewed,self.specs),reviewed)
        self.assertIn("Catalogue source review: reviewed.",generated.render_view(reviewed,self.specs))
        reviewed["review_fingerprint"]="0"*64
        self.assertIn("Catalogue source review: stale.",generated.render_view(reviewed,self.specs))

    def test_original_case_registration_and_shared_parameter_inputs_are_unchanged(self):
        old = Registry(ROOT)
        local_rules = {r["id"] for r in old.catalogues["7.8"]["requirements"]}
        del old.catalogues["7.8"]
        del old.accounting["7.8"]
        old.index["catalogues"].remove(generated.CATALOGUE)
        for rule in local_rules:
            del old.requirements[rule]
            del old.requirement_sections[rule]
        prior = [c for c in self.all_cases if c.rule not in local_rules]
        self.assertGreaterEqual(len(prior),1937)
        for case in prior:
            self.assertEqual(case.fingerprint(old),case.fingerprint(self.registry),case.name)
        shared = parameters.build_corpus()
        self.assertEqual((len(shared.cases),len(shared.files)),(66,105))
        self.assertFalse(set(shared.files)&set(self.files))
        for path,raw in shared.files.items():
            self.assertEqual(path.read_bytes(),raw)


if __name__=="__main__":
    unittest.main()
