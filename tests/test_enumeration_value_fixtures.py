"""Source-bound enumeration value, identity, access and observer countermodels."""
import copy
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
import generate_enumeration_value_fixtures as generated
import generate_derived_parameter_fixtures as parameters

EXPECTED = {
    "access": {
        "public-first": 1, "public-second": 2, "confirmed-first": 1, "unmodified-second": 2,
        "private-type-export": 2, "public-type-value": True, "public-type-ordinal": 2,
    },
    "order": {
        "list-first": 1, "list-second": 2, "list-third": 3,
        "split-first": 1, "split-second": 2, "split-third": 3,
        "list-order": True, "list-reverse": False, "split-order": True, "split-reverse": False,
        "single-ordinal": 1, "single-huge-value": True, "single-huge-ordinal": 1,
        "list-last-value": True, "list-last-ordinal": 3,
    },
    "construction": {
        "first:member": True, "first:ordinal": 1,
        "interior:member": True, "interior:ordinal": 2,
        "last:member": True, "last:ordinal": 3,
        "dynamic-second:member": True, "dynamic-second:ordinal": 2,
        "dynamic-third:member": True, "dynamic-third:ordinal": 3,
        "constant:member": True, "constant:ordinal": 2,
        "scalar-result:member": True, "scalar-result:ordinal": 2,
    },
}
NAMES = {
    "access": "S7_6_2_001_valid__enumeration_value_access",
    "order": "S7_6_2_002_valid__enumeration_value_order",
    "construction": "S7_6_2_003_valid__enumeration_value_construction",
}
CONSTRUCTOR_MEMBERS = {
    "first": "zulu_pick", "interior": "alpha_pick", "last": "mango_pick",
    "dynamic-second": "alpha_pick", "dynamic-third": "mango_pick",
    "constant": "alpha_pick", "scalar-result": "alpha_pick",
}
ACCESS = {
    "public_kind": "public", "zebra_default": "public", "apple_default": "public",
    "confirmed_kind": "public", "zebra_confirmed": "public", "apple_visible": "public", "mango_private": "private",
    "hidden_kind": "private", "hidden_zebra": "private", "exposed_apple": "public", "hidden_mango": "private",
}


class EnumerationValueFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {c.name: c for c in cls.all_cases if "/fixtures/enumeration_value_" in c.path}
        cls.catalogue = cls.registry.catalogues["7.6.2"]

    def spec(self, variant):
        return self.specs[NAMES[variant]]

    def inputs(self, variant):
        fixture = self.cases[NAMES[variant]].fixture
        return {name: (fixture.root / name).read_text() for name in fixture.files}

    def test_exact_three_shared_runtime_cases_and_eight_facets(self):
        self.assertEqual(set(self.specs), set(NAMES.values()))
        self.assertEqual(set(self.cases), set(NAMES.values()))
        self.assertEqual(sum(len(s["facets"]) for s in self.specs.values()), 8)
        self.assertEqual(sum(len(s["observations"]) for s in self.specs.values()), 36)
        for variant, expected in EXPECTED.items():
            name = NAMES[variant]
            spec, case = self.specs[name], self.cases[name]
            self.assertEqual({o["label"]: o["expected"] for o in spec["observations"]}, expected)
            self.assertEqual(spec["expected_check_count"], len(expected))
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.meta.evidence, "effect")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
            self.assertEqual(case.meta.images, 1)
            self.assertNotIn(case.rule, ("S7.6.2-004", "C1409"))
            manifest = json.loads(Path(case.path).read_text())
            self.assertEqual(manifest["expect"], {"phase": "run", "outcome": "success", "exit_code": 0})
            self.assertNotIn("requires", manifest)
            self.assertNotIn("oracle_profile", manifest)

    def test_exact_owned_generated_files_and_hermetic_build_order(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("enumeration_value_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.files))
        self.assertEqual(len(actual), 7)
        for path, content in self.files.items():
            self.assertEqual(path.read_bytes(), content)
            content.decode("ascii")
            self.assertTrue(content.endswith(b"\n"))
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, content.splitlines())), 132)
        access = self.cases[NAMES["access"]].fixture
        self.assertEqual(access.files, ["provider.f90", "client.f90"])
        self.assertEqual(access.build[1].depends_on, ["provider"])
        self.assertEqual(access.link["objects"], ["provider.o", "client.o"])
        self.assertNotEqual(self.inputs("order")["source.f90"], self.inputs("construction")["source.f90"])

    def parse_definitions(self, text):
        result = []
        for module, body in re.findall(r"(?ms)^module (\w+)\n(.*?)^end module \1\n", text):
            for access, name, contents in re.findall(
                    r"(?ms)^enumeration type(?:, (public|private))? :: (\w+)\n(.*?)^end enumeration type \2\n", body):
                self.assertNotIn("contains", body[:body.index("enumeration type")])
                groups = [line.split(", ") for line in re.findall(r"(?m)^enumerator :: (.+)$", contents)]
                self.assertTrue(groups)
                self.assertEqual(contents.count("enumerator"), len(groups))
                self.assertTrue(all(re.fullmatch(r"[a-z]\w*", name) for group in groups for name in group))
                result.append(generated.definition(module, name, groups, access or None))
        return result

    def test_actual_definitions_have_unique_names_separate_scopes_and_no_integer_enumerators(self):
        for variant in EXPECTED:
            text = "\n".join(self.inputs(variant).values())
            definitions = self.parse_definitions(text)
            self.assertEqual(definitions, self.spec(variant)["definitions"])
            seen = set()
            for d in definitions:
                for name in [d["name"]] + generated.members(d):
                    key = (d["module"], name.lower())
                    self.assertNotIn(key, seen)
                    seen.add(key)
            self.assertNotRegex(text, r"(?im)^enum\s*,")
            self.assertNotRegex(text, r"(?im)^enumerator.*=")
            self.assertNotRegex(text, r"(?i)\b(?:kind|c_sizeof|storage_size|transfer|next|previous)\s*\(")
            self.assertNotRegex(text, r"(?i)\b(?:bind\s*\(|iso_c_binding|class\s*\(|pointer\b|allocatable\b)")
            self.assertNotRegex(text, r"(?i)\b[bzo]['\"]")
            main = text.split("program p\n", 1)[1]
            self.assertNotIn("enumeration type", main)
            self.assertIn(f"call finish_checks({len(EXPECTED[variant])})", main)

    def test_declared_order_not_alphabetical_or_enum_zero_default(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            generated.members(generated.definition("m", "t", [["first"], ["FIRST"]]))
        definitions = self.spec("order")["definitions"]
        for d, names in zip(definitions[:2], (["zephyr", "amber", "maple"], ["walrus", "banana", "quail"])):
            self.assertEqual(generated.members(d), names)
            self.assertNotEqual(names, sorted(names))
            self.assertEqual([generated.ordinal(d, generated.enumeration_value(d, name)) for name in names], [1, 2, 3])
            accepted = 0
            for permutation in itertools.permutations(names):
                mutated = copy.deepcopy(d)
                mutated["groups"] = [list(permutation)]
                actual = [generated.ordinal(mutated, generated.enumeration_value(mutated, name)) for name in names]
                legal = actual == [1, 2, 3]
                self.assertEqual(legal, list(permutation) == names)
                accepted += legal
            self.assertEqual(accepted, 1)
        self.assertEqual(definitions[0]["groups"], [["zephyr", "amber", "maple"]])
        self.assertEqual(definitions[1]["groups"], [["walrus"], ["banana", "quail"]])
        single = definitions[2]
        value = generated.enumeration_value(single, "only_value")
        self.assertEqual(generated.ordinal(single, value), 1)
        self.assertEqual(generated.last_value(single, value), value)

    def test_huge_keeps_the_enumeration_type_and_uses_defined_values(self):
        d = self.spec("order")["definitions"][0]
        first, last = generated.enumeration_value(d, "zephyr"), generated.enumeration_value(d, "maple")
        actual = generated.last_value(d, first)
        self.assertEqual(actual, last)
        self.assertIsInstance(actual, generated.EnumerationValue)
        self.assertEqual(generated.ordinal(d, actual), 3)
        with self.assertRaises(TypeError):
            generated.ordinal(d, 3)
        foreign = self.spec("order")["definitions"][1]
        foreign_last = generated.enumeration_value(foreign, "quail")
        with self.assertRaises(TypeError):
            generated.same_value(d, last, foreign_last)
        text = self.inputs("order")["source.f90"]
        self.assertEqual(set(re.findall(r"\bhuge\((\w+)\)", text)), {"zephyr", "only_value"})
        self.assertNotIn("huge(1)", text)

    def test_accessibility_truth_table_and_no_duplicate_explicit_attributes(self):
        spec = self.spec("access")
        self.assertEqual(generated.accessibility(spec["definitions"], "private", spec["explicit_access"]), ACCESS)
        self.assertTrue(all(ACCESS[name] == "public" for name in spec["client_imports"]))
        self.assertEqual(ACCESS["hidden_kind"], "private")
        self.assertEqual(ACCESS["exposed_apple"], "public")
        for default, header in itertools.product(("public", "private"), (None, "public", "private")):
            d = generated.definition("m", "t", [["zeta", "alpha"]], header)
            expected = header or default
            state = generated.accessibility([d], default, [])
            self.assertEqual(state, {"t": expected, "zeta": expected, "alpha": expected})
            opposite = "private" if expected == "public" else "public"
            state = generated.accessibility([d], default, [("zeta", expected), ("alpha", opposite)])
            self.assertEqual(state["zeta"], expected)
            self.assertEqual(state["alpha"], opposite)
        for statements in (spec["explicit_access"] + [("public_kind", "public")],
                           spec["explicit_access"] + [("zebra_confirmed", "private")]):
            with self.assertRaisesRegex(ValueError, "duplicate explicit"):
                generated.accessibility(spec["definitions"], "private", statements)

    def test_actual_provider_access_and_exported_private_type_constant_usage(self):
        inputs = self.inputs("access")
        provider, client = inputs["provider.f90"], inputs["client.f90"]
        self.assertIn("implicit none\nprivate\n", provider)
        statements = [(name, access) for access, name in re.findall(r"(?m)^(public|private) :: (\w+)$", provider)]
        self.assertEqual(statements, self.spec("access")["explicit_access"])
        self.assertEqual(generated.accessibility(self.parse_definitions(provider), "private", statements), ACCESS)
        joined = client.replace("&\n    ", "")
        imports = re.search(r"(?m)^use enumeration_provider, only: (.+)$", joined)[1].split(", ")
        self.assertEqual(imports, self.spec("access")["client_imports"])
        for private in ("hidden_kind", "hidden_zebra", "hidden_mango", "mango_private"):
            self.assertNotRegex(client, rf"\b{private}\b")
        self.assertIn("type(public_kind) :: public_value\npublic_value=apple_default", client)
        self.assertIn("int(exposed_apple),2)", client)
        for name in ("public_kind", "confirmed_kind", "hidden_kind"):
            self.assertNotRegex(provider, rf"(?m)^(?:public|private) :: {name}$")

    def constructor_flow(self, source):
        d = self.spec("construction")["definitions"][0]
        parameter = re.search(r"(?m)^type\(selection_kind\), parameter :: fixed_middle=selection_kind\((\d+)\)$", source)
        self.assertIsNotNone(parameter)
        self.assertEqual(parameter[1], "2")
        fixed = generated.construct(d, int(parameter[1]))
        observer = source.split("subroutine observe_selection(", 1)[1].split("end subroutine observe_selection", 1)[0]
        self.assertIn("type(selection_kind), intent(in) :: actual,expected\n", observer)
        self.assertIn("call check_logical(label//':member',actual==expected,.true.)", observer)
        self.assertIn("call check_integer(label//':ordinal',int(actual),expected_ordinal)", observer)
        self.assertNotIn("print", observer.lower())
        self.assertNotIn("class(", observer.lower())
        main = source.split("program p\n", 1)[1]
        self.assertIn("type(selection_kind) :: value", main)
        self.assertIn("integer :: index\n", main)
        self.assertNotRegex(main, r"(?im)^integer,.*parameter.*index")
        index = value = None
        assignments, observations, labels = [], {}, []
        for line in main.splitlines():
            match = re.fullmatch(r"index=(\d+)", line)
            if match:
                index = int(match[1])
                assignments.append(index)
                self.assertIn(index, (2, 3))
                continue
            match = re.fullmatch(r"value=selection_kind\((\d+|index)\)", line)
            if match:
                position = index if match[1] == "index" else int(match[1])
                self.assertIsNotNone(position)
                value = generated.construct(d, position)
                continue
            if line.startswith("value="):
                self.fail("enumeration value was replaced by an INTEGER/nonconstructor assignment")
            match = re.fullmatch(r"call observe_selection\('([^']+)',(value|fixed_middle|selection_kind\(index\)),(\w+),(\d+)\)", line)
            if not match:
                continue
            label, expression, expected_member, expected_ordinal = match.groups()
            labels.append(label)
            self.assertEqual(expected_member, CONSTRUCTOR_MEMBERS[label])
            self.assertEqual(int(expected_ordinal), EXPECTED["construction"][label + ":ordinal"])
            if expression == "value":
                self.assertIsNotNone(value)
                actual = value
            elif expression == "fixed_middle":
                actual = fixed
            else:
                self.assertIsNotNone(index)
                actual = generated.construct(d, index)
            expected = generated.enumeration_value(d, expected_member)
            observations[label + ":member"] = generated.same_value(d, actual, expected)
            observations[label + ":ordinal"] = generated.ordinal(d, actual)
        self.assertEqual(assignments, [2, 3, 2])
        self.assertEqual(labels, list(CONSTRUCTOR_MEMBERS))
        self.assertEqual(observations, EXPECTED["construction"])
        self.assertIn("call finish_checks(14)", main)
        return observations

    def test_actual_constructor_flow_defines_indices_values_and_consumes_parameter_and_scalar_results(self):
        self.constructor_flow(self.inputs("construction")["source.f90"])
        spec = self.spec("construction")
        self.assertEqual([stage["index"] for stage in spec["stages"]], [1, 2, 3, 2, 3, 2, 2])
        self.assertEqual([stage["origin"] for stage in spec["stages"]],
                         ["literal", "literal", "literal", "variable", "variable", "parameter", "scalar-expression"])

    def test_constructor_named_value_oracle_rejects_inverse_roundtrip_cancellation(self):
        spec = self.spec("construction")
        d = spec["definitions"][0]
        named = {1: "zulu_pick", 2: "alpha_pick", 3: "mango_pick"}
        for index, expected_member in named.items():
            self.assertEqual(generated.construct(d, index), generated.enumeration_value(d, expected_member))
        for permutation in itertools.permutations(list(named.values())):
            named_match = [permutation[i-1] == named[i] for i in (1, 2, 3)]
            inverse_roundtrip = [i for i in (1, 2, 3)]
            self.assertEqual(inverse_roundtrip, [1, 2, 3])
            self.assertEqual(all(named_match), list(permutation) == list(named.values()))
        wrong = dict(EXPECTED["construction"])
        wrong["first:member"] = False
        self.assertFalse(generated.accepts(spec["observations"], wrong))
        for invalid in (None, True, [2], 2.0):
            with self.assertRaises(TypeError):
                generated.construct(d, invalid)
        for invalid in (0, 4):
            with self.assertRaises(ValueError):
                generated.construct(d, invalid)

    def test_constructor_source_guards_detect_uninitialized_index_type_and_observer_mutations(self):
        original = self.inputs("construction")["source.f90"]
        mutations = [
            original.replace("index=2\nvalue=selection_kind(index)", "value=selection_kind(index)", 1),
            original.replace("value=selection_kind(1)", "value=1", 1),
            original.replace("fixed_middle=selection_kind(2)", "fixed_middle=alpha_pick", 1),
            original.replace("type(selection_kind), intent(in)", "class(selection_kind), intent(in)", 1),
            original.replace("call check_logical(label//':member',actual==expected,.true.)\n", "", 1),
            original.replace("'first',value,zulu_pick,1", "'first',value,alpha_pick,1", 1),
        ]
        for source in mutations:
            self.assertNotEqual(source, original)
            with self.assertRaises(AssertionError):
                self.constructor_flow(source)

    def test_all_observers_reject_missing_extra_wrong_and_integer_logical_confusion(self):
        for variant, expected in EXPECTED.items():
            spec = self.spec(variant)
            self.assertTrue(generated.accepts(spec["observations"], expected))
            self.assertFalse(generated.accepts(spec["observations"], {}))
            self.assertFalse(generated.accepts(spec["observations"], dict(expected, phantom=1)))
            for label, value in expected.items():
                absent = dict(expected)
                del absent[label]
                self.assertFalse(generated.accepts(spec["observations"], absent))
                wrong = not value if type(value) is bool else value + 1
                self.assertFalse(generated.accepts(spec["observations"], dict(expected, **{label: wrong})))
                wrong_type = int(value) if type(value) is bool else True
                self.assertFalse(generated.accepts(spec["observations"], dict(expected, **{label: wrong_type})))

    def test_emitted_primitive_guards_counts_and_nonvacuous_main_calls(self):
        for variant in EXPECTED:
            source = "\n".join(self.inputs(variant).values())
            checker = source[source.index("module enumeration_checks\n"):].split("end module enumeration_checks\n", 1)[0]
            self.assertEqual(checker + "end module enumeration_checks\n", generated.CHECKS)
            self.assertIn("integer, save :: checked=0", checker)
            self.assertIn("if (actual/=expected) then", checker)
            self.assertIn("if (actual .neqv. expected) then", checker)
            self.assertIn("if (checked/=expected) then", checker)
            self.assertEqual(checker.count("checked=checked+1"), 2)
            main = source.split("program p\n", 1)[1]
            self.assertEqual(main.count("call finish_checks("), 1)
            self.assertIn(f"call finish_checks({len(EXPECTED[variant])})", main)
            self.assertGreater(len(EXPECTED[variant]), 0)
            if variant != "construction":
                actual = {}
                for category, label, expression, expected in re.findall(
                        r"(?m)^call check_(integer|logical)\('([^']+)',(.+),([^.][0-9]*|\.true\.|\.false\.)\)$", main):
                    actual[label] = expected == ".true." if category == "logical" else int(expected)
                self.assertEqual(actual, EXPECTED[variant])

    def test_full_pending_maps_and_phase_admin_preserving_views(self):
        self.assertEqual(len(self.catalogue["requirements"]), 13)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 52)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 44)
        for requirement in self.catalogue["requirements"]:
            covered = set(generated.ELIGIBLE.get(requirement["id"], []))
            self.assertEqual(set(requirement["pending"]), set(requirement["facets"]) - covered)
        range_rule = next(r for r in self.catalogue["requirements"] if r["id"] == "S7.6.2-004")
        self.assertEqual(set(range_rule["pending"]), set(range_rule["facets"]))
        self.assertEqual(len(range_rule["pending"]), 3)
        self.assertEqual(generated.synced_catalogue(self.catalogue, self.specs), self.catalogue)
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue, self.specs))
        native = Registry(ROOT)
        native.catalogues = {"7.6.2": self.catalogue}
        native.render()
        appendix = view.split("## Complete finite pending plans\n", 1)[1].split("## Reproduction and remaining gates", 1)[0]
        self.assertEqual(appendix.count("* **`"), 44)
        for requirement in self.catalogue["requirements"]:
            for facet, plan in requirement["pending"].items():
                self.assertIn(f"* **`{facet}`** - {plan}", appendix)
        reviewed = copy.deepcopy(self.catalogue)
        reviewed.update(review_state="reviewed", review_rationale="Synthetic in-memory state, not an approval.")
        native = Registry(ROOT)
        native.catalogues["7.6.2"] = reviewed
        reviewed["review_fingerprint"] = native.catalogue_fingerprint("7.6.2")
        self.assertEqual(generated.synced_catalogue(reviewed, self.specs), reviewed)
        self.assertIn("Catalogue source review: reviewed.", generated.render_view(reviewed, self.specs))
        reviewed["review_fingerprint"] = "0" * 64
        self.assertIn("Catalogue source review: stale.", generated.render_view(reviewed, self.specs))

    def test_original_case_registration_and_shared_parameter_inputs_are_unchanged(self):
        old = Registry(ROOT)
        local_rules = {r["id"] for r in old.catalogues["7.6.2"]["requirements"]}
        del old.catalogues["7.6.2"]
        del old.accounting["7.6.2"]
        old.index["catalogues"].remove(generated.CATALOGUE)
        for rule in local_rules:
            del old.requirements[rule]
            del old.requirement_sections[rule]
        existing = [c for c in self.all_cases if c.rule not in local_rules]
        self.assertGreaterEqual(len(existing), 1907)
        for case in existing:
            self.assertEqual(case.fingerprint(old), case.fingerprint(self.registry), case.name)
        shared = parameters.build_corpus()
        self.assertEqual((len(shared.cases), len(shared.files)), (66, 105))
        self.assertFalse(set(shared.files) & set(self.files))
        for path, contents in shared.files.items():
            self.assertEqual(path.read_bytes(), contents)


if __name__ == "__main__":
    unittest.main()
