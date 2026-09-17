"""Independent entry, definedness, literal-oracle and source-partition regressions."""
import copy
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_type_parameter_entry_fixtures as generated

PARTITION = {
    "procedures": ["procedure-selector-snapshot", "procedure-entity-length-snapshot"],
    "blocks": ["block-selector-snapshot", "block-entity-length-snapshot"],
    "post_undefinition": ["post-undefinition-snapshot"],
    "fresh_entries": ["fresh-entry-captures"],
    "nested_blocks": ["nested-block-snapshots"],
}
COUNTS = {"procedures": 9, "blocks": 9, "post_undefinition": 10, "fresh_entries": 18, "nested_blocks": 11}
LENGTHS = {
    "procedure_selector:length": 2, "procedure_entity:length": 3,
    "block_selector:length": 3, "block_entity:length": 2,
    "undefined_procedure:length": 3, "undefined_block:length": 3,
    "fresh_procedure_first:length": 2, "fresh_procedure_second:length": 4,
    "fresh_block_first:length": 3, "fresh_block_second:length": 5,
    "nested_outer:length": 3, "nested_inner:length": 5, "nested_outer_after_inner:length": 3,
}
ENTRY_VALUES = {
    "procedures": [2, 3], "blocks": [3, 2], "post_undefinition": [3, 3],
    "fresh_entries": [2, 4, 3, 5], "nested_blocks": [3, 5],
}
PAYLOADS = {
    "procedures": ["ab", "abc"], "blocks": ["abc", "ab"], "post_undefinition": ["abc", "abc"],
    "fresh_entries": ["ab", "abcd", "abc", "abcde"], "nested_blocks": ["abc", "abcde"],
}


class TypeParameterEntryFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {case.name: case for case in cls.all_cases if "/fixtures/type_parameter_entry_" in case.path}

    def spec(self, variant):
        return self.specs[generated.identifier(variant)]

    def source(self, variant):
        return (self.cases[generated.identifier(variant)].fixture.root / "source.f90").read_text()

    def procedure(self, source, name):
        match = re.search(rf"(?ms)^subroutine {name}\(n\)\n(.*?)^end subroutine {name}$", source)
        self.assertIsNotNone(match)
        return match[1]

    def require_snapshot(self, body, prefix, local, payload, changed, expected, undefined=False):
        assigned = f"{local}='{payload}'\n"
        mutation = "call undefine(n)\n" if undefined else f"n={changed}\n"
        length = f"call check_integer('{prefix}:length',len({local}),{expected})"
        value = f"call check_logical('{prefix}:payload',{local}=='{payload}',.true.)"
        for fragment in (assigned, mutation, length, value):
            self.assertIn(fragment, body)
        self.assertLess(body.index(assigned), body.index(mutation))
        self.assertLess(body.index(mutation), body.index(length))
        self.assertLess(body.index(length), body.index(value))

    def verify_source(self, variant, source):
        self.assertTrue(source.startswith("program p\nimplicit none\ninteger :: checked\n"))
        self.assertTrue(source.endswith(generated.CHECKERS + "end program p\n"))
        self.assertIn("\nchecked=0\n", source)
        self.assertNotRegex(source, r"(?im)^\s*(?:data|save|use|implicit\s+(?!none))\b")
        self.assertNotRegex(source, r"(?i)\b(?:pointer|allocatable|optional|parameter|volatile|asynchronous|value|common|equivalence)\s*(?:::|,)")
        self.assertNotRegex(source, r"(?i)\b(?:rank|kind|size|storage_size|c_sizeof|associated|allocated|transfer|repeat)\s*\(")
        self.assertNotRegex(source, r"(?i)\b(?:class|type)\s*\(")
        target_declarations = [line for line in source.splitlines() if line.startswith("character") and ":: label" not in line]
        allowed = {"character(len=n) :: text", "character :: text*(n)",
                   "character(len=n) :: outer_text", "character(len=n) :: inner_text"}
        self.assertTrue(target_declarations)
        self.assertTrue(all(line in allowed for line in target_declarations))
        self.assertTrue(all("=" not in line.split("::", 1)[1] for line in target_declarations))
        self.assertEqual(source.count("call finish_checks("), 1)
        self.assertIn(f"call finish_checks({COUNTS[variant]})", source)
        for guard in self.spec(variant)["primitive_guards"]:
            self.assertIn(generated.guard_code(guard), source)
        if variant == "procedures":
            self.assertIn("entries=0\nn=2\ncall procedure_selector(n)\nn=3\ncall procedure_entity(n)\n", source)
            self.assertEqual(source.count("call procedure_selector(n)"), 1)
            self.assertEqual(source.count("call procedure_entity(n)"), 1)
            for name, declaration, payload, changed, expected in (
                ("procedure_selector", "character(len=n) :: text", "ab", 5, 2),
                ("procedure_entity", "character :: text*(n)", "abc", 7, 3),
            ):
                body = self.procedure(source, name)
                self.assertTrue(body.startswith("integer, intent(inout) :: n\n" + declaration + "\n"))
                self.require_snapshot(body, name, "text", payload, changed, expected)
        elif variant == "blocks":
            for name, initial, declaration, payload, changed, expected in (
                ("block_selector", 3, "character(len=n) :: text", "abc", 7, 3),
                ("block_entity", 2, "character :: text*(n)", "ab", 5, 2),
            ):
                self.assertIn(f"n={initial}\n{name}: block\n{declaration}\n", source)
                body = source.split(name + ": block\n", 1)[1].split("end block " + name, 1)[0]
                self.require_snapshot(body, name, "text", payload, changed, expected)
        elif variant == "post_undefinition":
            self.assertIn("n=3\ncall undefined_procedure(n)\nn=3\nundefined_block: block\n", source)
            self.assertEqual(source.count("call undefine(n)"), 2)
            helper = re.search(r"(?ms)^subroutine undefine\(x\)\n(.*?)^end subroutine undefine$", source)
            self.assertIsNotNone(helper)
            self.assertEqual(helper[1], "integer, intent(out) :: x\nundefinition_calls=undefinition_calls+1\n")
            self.assertIn("undefinition_calls=0\n", source)
            for name, body, restored in (
                ("undefined_procedure", self.procedure(source, "undefined_procedure"), 5),
                ("undefined_block", source.split("undefined_block: block\n", 1)[1].split("end block undefined_block", 1)[0], 7),
            ):
                self.require_snapshot(body, name, "text", "abc", None, 3, True)
                self.assertIn(f"n={restored}\ncall check_integer('{name}:restored',n,{restored})", body)
                interval = body.split("call undefine(n)\n", 1)[1].split(f"n={restored}\n", 1)[0]
                self.assertNotRegex(interval, r"\bn\b")
                self.assertEqual(interval.count("call check_"), 2)
        elif variant == "fresh_entries":
            self.assertIn("n=2\ncall capture_fresh(n)\nn=4\ncall capture_fresh(n)\n", source)
            self.assertEqual(source.count("call capture_fresh(n)"), 2)
            self.assertEqual(source.count("subroutine capture_fresh(n)"), 1)
            self.assertEqual(source.count("reentered: block"), 1)
            self.assertIn("do iteration=1,2\nif (iteration==1) then\nn=3\nelse\nn=5\nend if\nreentered: block\n", source)
            self.assertIn("end block reentered\nend do\n", source)
            self.assertEqual(source.count("case default"), 2)
            procedure = self.procedure(source, "capture_fresh")
            self.assertTrue(procedure.startswith("integer, intent(inout) :: n\ncharacter(len=n) :: text\n"))
            block = source.split("reentered: block\n", 1)[1].split("end block reentered", 1)[0]
            for region, prefix, expectations in (
                (procedure, "fresh_procedure", [("ab", 2), ("abcd", 4)]),
                (block, "fresh_block", [("abc", 3), ("abcde", 5)]),
            ):
                for order, (payload, expected) in enumerate(expectations, 1):
                    body = region.split(f"case({order})\n", 1)[1].split("case", 1)[0]
                    name = prefix + ("_first" if order == 1 else "_second")
                    self.require_snapshot(body, name, "text", payload, 7, expected)
        elif variant == "nested_blocks":
            self.assertIn("n=3\nouter_scope: block\ncharacter(len=n) :: outer_text\n", source)
            self.assertIn("outer_text='abc'\nn=5\n", source)
            self.assertIn("inner_scope: block\ncharacter(len=n) :: inner_text\n", source)
            self.assertIn("inner_text='abcde'\nn=7\n", source)
            inner = source.split("inner_scope: block\n", 1)[1].split("end block inner_scope", 1)[0]
            for local, prefix, expected, payload in (
                ("outer_text", "nested_outer", 3, "abc"), ("inner_text", "nested_inner", 5, "abcde"),
            ):
                self.assertIn(f"call check_integer('{prefix}:length',len({local}),{expected})", inner)
                self.assertIn(f"call check_logical('{prefix}:payload',{local}=='{payload}',.true.)", inner)
            after = source.split("end block inner_scope\n", 1)[1].split("end block outer_scope", 1)[0]
            self.assertNotIn("len(inner_text)", after)
            self.assertNotIn("inner_text==", after)

    def test_exact_five_program_seven_facet_run_partition(self):
        self.assertEqual(set(self.cases), {generated.identifier(variant) for variant in PARTITION})
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 7)
        self.assertEqual(sum(spec["expected_check_count"] for spec in self.specs.values()), 57)
        for variant, facets in PARTITION.items():
            spec, case = self.spec(variant), self.cases[generated.identifier(variant)]
            self.assertEqual(spec["facets"], facets)
            self.assertEqual(spec["expected_check_count"], COUNTS[variant])
            self.assertEqual(case.rule, "S8.3-001")
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard), ("valid", "effect", "f2023"))
            self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.exit_code), ("run", 0))
            self.assertEqual(case.meta.profiles, [])
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)

    def test_independent_literal_lengths_payloads_and_entry_inputs(self):
        actual = {guard["label"]: guard["expected"] for spec in self.specs.values()
                  for guard in spec["primitive_guards"] if guard["family"] in ("captured-length", "post-undefinition-length")}
        self.assertEqual(actual, LENGTHS)
        for variant in PARTITION:
            entries = self.spec(variant)["entry_plan"]
            self.assertEqual([entry["entry_value"] for entry in entries], ENTRY_VALUES[variant])
            self.assertEqual([entry["payload"] for entry in entries], PAYLOADS[variant])
            for entry in entries:
                self.assertEqual(type(entry["entry_value"]), int)
                self.assertEqual(type(entry["expected_length"]), int)
                self.assertEqual(entry["source"], "n")

    def test_actual_sources_have_valid_local_declarations_and_defined_state_order(self):
        for variant in PARTITION:
            with self.subTest(variant=variant):
                self.verify_source(variant, self.source(variant))

    def test_fixed_lengths_initializers_optional_or_OUT_sources_are_rejected_by_source_regressions(self):
        for variant in PARTITION:
            source = self.source(variant)
            for altered in (
                source.replace("character(len=n)", "character(len=3)"),
                source.replace("character(len=n) :: text", "character(len=n) :: text='abc'"),
            ):
                if altered != source:
                    with self.assertRaises(AssertionError):
                        self.verify_source(variant, altered)
        source = self.source("procedures")
        for altered in (
            source.replace("integer, intent(inout) :: n", "integer, intent(out) :: n"),
            source.replace("integer, intent(inout) :: n", "integer, optional, intent(inout) :: n"),
            source.replace("character :: text*(n)", "character :: text*n"),
        ):
            with self.assertRaises(AssertionError):
                self.verify_source("procedures", altered)

    def test_payloads_must_be_defined_before_mutation_and_reads(self):
        for variant in PARTITION:
            source = self.source(variant)
            for line in set(re.findall(r"(?m)^(?:text|outer_text|inner_text)='[^']*'\n", source)):
                with self.assertRaises(AssertionError):
                    self.verify_source(variant, source.replace(line, "", 1))

    def test_undefined_source_is_never_observed_and_helper_does_not_define_it(self):
        source = self.source("post_undefinition")
        for altered in (
            source.replace("integer, intent(out) :: x", "integer, intent(inout) :: x"),
            source.replace("undefinition_calls=undefinition_calls+1", "x=0\nundefinition_calls=undefinition_calls+1"),
            source.replace("call undefine(n)\n", "call undefine(n)\ncall check_integer('bad-read',n,3)\n", 1),
            source.replace("n=5\ncall check_integer('undefined_procedure:restored'", "call check_integer('undefined_procedure:restored'"),
            source.replace("call undefine(n)\n", "", 1),
        ):
            with self.assertRaises(AssertionError):
                self.verify_source("post_undefinition", altered)

    def test_missing_extra_reordered_entries_and_fixed_first_capture_do_not_pass(self):
        source = self.source("fresh_entries")
        for altered in (
            source.replace("n=4\ncall capture_fresh(n)\n", ""),
            source.replace("n=4\ncall capture_fresh(n)\n", "n=4\ncall capture_fresh(n)\ncall capture_fresh(n)\n"),
            source.replace("n=2\ncall capture_fresh(n)", "n=4\ncall capture_fresh(n)"),
            source.replace("do iteration=1,2", "do iteration=1,1"),
            source.replace("fresh_procedure_second:length',len(text),4", "fresh_procedure_second:length',len(text),2"),
            source.replace("fresh_block_second:length',len(text),5", "fresh_block_second:length',len(text),3"),
        ):
            with self.assertRaises(AssertionError):
                self.verify_source("fresh_entries", altered)
        self.assertNotEqual([2, 2, 3, 3], ENTRY_VALUES["fresh_entries"])

    def test_nested_parameters_are_not_current_source_or_same_as_each_other(self):
        self.assertEqual(ENTRY_VALUES["nested_blocks"], [3, 5])
        self.assertNotEqual([7, 7], ENTRY_VALUES["nested_blocks"])
        self.assertNotEqual([3, 3], ENTRY_VALUES["nested_blocks"])
        source = self.source("nested_blocks")
        for altered in (
            source.replace("nested_outer:length',len(outer_text),3", "nested_outer:length',n,3"),
            source.replace("nested_inner:length',len(inner_text),5", "nested_inner:length',len(outer_text),5"),
            source.replace("outer_text='abc'\nn=5\n", "outer_text='abc'\nn=7\n"),
        ):
            with self.assertRaises(AssertionError):
                self.verify_source("nested_blocks", altered)

    def test_all_scalar_guards_reject_missing_extra_wrong_and_type_confused_observations(self):
        for spec in self.specs.values():
            correct = {guard["label"]: guard["expected"] for guard in spec["primitive_guards"]}
            self.assertTrue(generated.accepts(spec["primitive_guards"], correct))
            self.assertFalse(generated.accepts(spec["primitive_guards"], {}))
            self.assertFalse(generated.accepts(spec["primitive_guards"], dict(correct, extra=1)))
            for label, expected in correct.items():
                missing = dict(correct)
                del missing[label]
                self.assertFalse(generated.accepts(spec["primitive_guards"], missing))
                wrong = not expected if type(expected) is bool else expected + 1
                self.assertFalse(generated.accepts(spec["primitive_guards"], dict(correct, **{label: wrong})))
                wrong_type = int(expected) if type(expected) is bool else True
                self.assertFalse(generated.accepts(spec["primitive_guards"], dict(correct, **{label: wrong_type})))

    def test_exact_source_bound_expected_spans_and_positive_completion_counts(self):
        total = 0
        for variant in PARTITION:
            source, spec = self.source(variant), self.spec(variant)
            lines = source.splitlines()
            self.assertEqual(len(spec["guard_bindings"]), COUNTS[variant] + 1)
            self.assertEqual(set(spec["sensitivity_representatives"]), {g["family"] for g in spec["guard_bindings"]})
            for guard in spec["guard_bindings"]:
                line = lines[guard["line"] - 1]
                self.assertEqual(line, guard["source_text"])
                first, last = guard["first_column"] - 1, guard["last_column"]
                self.assertEqual(line[first:last], guard["expected_text"])
                wrong = generated.literal(not guard["expected"] if type(guard["expected"]) is bool else guard["expected"] + 1)
                altered = line[:first] + wrong + line[last:]
                self.assertNotEqual(altered, line)
                self.assertEqual(altered[:first], line[:first])
                self.assertTrue(altered.endswith(line[last:]))
                total += 1
        self.assertEqual(total, 62)

    def test_exact_files_native_render_and_all_unselected_source_plans_remain(self):
        actual = {path for path in (ROOT / "tests/fixtures").glob("type_parameter_entry_*/*") if path.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 10)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
            raw.decode("ascii")
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, raw.splitlines())), 132)
        catalogue = self.registry.catalogues["8.3"]
        self.assertEqual(len(catalogue["requirements"]), 2)
        self.assertEqual(sum(len(r["facets"]) for r in catalogue["requirements"]), 18)
        self.assertEqual(sum(len(r["pending"]) for r in catalogue["requirements"]), 11)
        self.assertEqual(sum(map(len, catalogue["subunits"].values())), 19)
        self.assertEqual(len(catalogue["accounting"]), 22)
        c814, entry = catalogue["requirements"]
        self.assertEqual(set(c814["pending"]), set(c814["facets"]))
        self.assertEqual(set(entry["pending"]), {"pdt-length-snapshot", "fixed-length-descriptor-snapshot"})
        self.assertEqual(sum(len(r["pending"]) for r in self.registry.catalogues["8.4"]["requirements"]), 35)
        self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
        self.assertEqual(generated.render_view(catalogue, self.specs), (ROOT / generated.VIEW).read_text())
        native = Registry(ROOT)
        native.catalogues = {"8.3": catalogue}
        native.render()
        reviewed = copy.deepcopy(catalogue)
        reviewed["review_rationale"] = "In-memory source-administration preservation regression, not an approval."
        self.assertEqual(generated.synced_catalogue(reviewed)["review_rationale"], reviewed["review_rationale"])

    def test_view_tracks_source_state_without_inventing_fixture_adjudication(self):
        for state in ("draft", "reviewed", "stale"):
            with self.subTest(state=state):
                catalogue = copy.deepcopy(self.registry.catalogues["8.3"])
                catalogue["review_state"] = "draft" if state == "draft" else "reviewed"
                catalogue["review_rationale"] = "Synthetic source state; no persisted approval."
                registry = Registry(ROOT)
                registry.catalogues["8.3"] = catalogue
                catalogue["review_fingerprint"] = (
                    "0" * 64 if state == "stale" else registry.catalogue_fingerprint("8.3"))
                view = generated.render_view(catalogue, self.specs)
                self.assertIn(f"**Source review: {state}.**", view)
                self.assertNotIn("fixture packet UNAPPROVED", view)
                self.assertIn("Current fixture/evidence adjudications are separate", view)
                self.assertIn("9 C814 facets and 2 other S8.3-001 facets remain PENDING.", view)
                self.assertIn("This packet changes no8.4source, fixture or facet.", view)
                self.assertEqual(generated.synced_catalogue(catalogue), catalogue)


if __name__ == "__main__":
    unittest.main()
