"""Finite overriding identity countermodels and guards on the actual runtime inputs."""
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
import generate_type_overriding_fixtures as generated
import generate_derived_parameter_fixtures as parameters


EXPECTED = {
    "same_binding": [
        ("parent-direct", "base%work()", 11),
        ("parent-helper", "dispatch(base)", 11),
        ("child-helper", "dispatch(extended)", 22),
        ("explicit-parent", "extended%parent%work()", 11),
        ("child-direct", "extended%work()", 22)],
    "different_binding": [
        ("parent-direct", "base%work()", 11),
        ("inherited-direct", "extended%work()", 11),
        ("inherited-helper", "dispatch(extended)", 11),
        ("extra-direct", "extended%extra()", 33)],
    "private_homonym": [
        ("private-parent-helper", "dispatch(base)", 7),
        ("private-child-helper", "dispatch(extended)", 7),
        ("public-homonym", "extended%work()", 9)],
    "accessible_private": [
        ("private-parent-helper", "dispatch(base)", 11),
        ("overridden-child-helper", "dispatch(extended)", 22),
        ("public-child", "extended%work()", 22)],
    "override_then_inherit": [
        ("root-direct", "original%work()", 11),
        ("root-helper", "dispatch(original)", 11),
        ("grand-helper", "dispatch(last)", 22),
        ("grand-direct", "last%work()", 22)],
    "inherit_then_override": [
        ("root-direct", "original%work()", 11),
        ("root-helper", "dispatch(original)", 11),
        ("leaf-helper", "dispatch(last)", 33),
        ("explicit-middle", "last%middle%work()", 11),
        ("leaf-direct", "last%work()", 33)],
}
FACETS = {
    "same_binding": ["same-binding-different-target", "explicit-parent-component-call"],
    "different_binding": ["different-binding-name"],
    "private_homonym": ["inaccessible-private-homonym"],
    "accessible_private": ["accessible-private-parent"],
    "override_then_inherit": ["override-then-inherit"],
    "inherit_then_override": ["inherit-then-override"],
}
FIELDS = {"parent_token": 17, "root_token": 17, "child_token": 29, "leaf_token": 41}
SHAPES = {
    "same_binding": {"parent": (None, ["parent_token"]), "child": ("parent", ["child_token"])},
    "different_binding": {"parent": (None, ["parent_token"]), "child": ("parent", ["child_token"])},
    "private_homonym": {"parent": (None, ["parent_token"]), "child": ("parent", [])},
    "accessible_private": {"parent": (None, ["parent_token"]), "child": ("parent", ["child_token"])},
    "override_then_inherit": {"root": (None, ["root_token"]), "child": ("root", ["child_token"]),
                              "grand": ("child", [])},
    "inherit_then_override": {"root": (None, ["root_token"]), "middle": ("root", []),
                              "leaf": ("middle", ["leaf_token"])},
}


class TypeOverridingFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.catalogue = cls.registry.catalogues["7.5.7.3"]
        cls.cases = {c.name: c for c in runner.collect_cases(ROOT / "tests", cls.registry)
                     if "/fixtures/type_overriding_" in c.path}

    def name(self, variant):
        rule = "S7.5.7.3-011" if variant in ("override_then_inherit", "inherit_then_override") else "S7.5.7.3-001"
        return generated.identifier(rule, variant)

    def source(self, variant):
        return (self.cases[self.name(variant)].fixture.root / "source.f90").read_text()

    def spec(self, variant):
        return self.specs[self.name(variant)]

    def test_exact_ids_primary_facets_and_runtime_only_contracts(self):
        expected_names = {self.name(variant) for variant in EXPECTED}
        self.assertEqual(set(self.specs), expected_names)
        self.assertEqual(set(self.cases), expected_names)
        self.assertEqual(len(expected_names), 6)
        self.assertEqual(sum(map(len, FACETS.values())), 7)
        self.assertEqual(sum(map(len, EXPECTED.values())), 24)
        for variant, expected in EXPECTED.items():
            name = self.name(variant)
            case, spec = self.cases[name], self.specs[name]
            with self.subTest(case=name):
                self.assertEqual(spec["facets"], FACETS[variant])
                self.assertEqual([(o["label"], o["expression"], o["expected"]) for o in spec["observations"]], expected)
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.meta.evidence, "effect")
                self.assertEqual(case.meta.standard, "f2023")
                self.assertEqual(case.meta.oracle_basis, "standard")
                self.assertFalse(case.meta.profiles)
                self.assertFalse(case.meta.coarray)
                self.assertEqual(case.meta.images, 1)
                manifest = json.loads((case.fixture.root / "fixture.json").read_text())
                self.assertEqual(manifest["expect"], {"phase": "run", "outcome": "success", "exit_code": 0})
                self.assertNotIn("requires", manifest)
                self.assertNotIn("diagnostic", manifest["expect"])
                self.assertNotIn(case.rule, ("C789", "C790"))

    def test_exact_scoped_files_and_shared_case_not_duplicate_programs(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("type_overriding_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.outputs))
        self.assertEqual(len(actual), 12)
        for path, content in self.outputs.items():
            self.assertEqual(path.read_bytes(), content)
            content.decode("ascii")
            self.assertTrue(content.endswith(b"\n"))
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, content.splitlines())), 132)
        owners = {facet: [name for name, spec in self.specs.items() if facet in spec["facets"]]
                  for facets in FACETS.values() for facet in facets}
        self.assertEqual(owners["same-binding-different-target"], [self.name("same_binding")])
        self.assertEqual(owners["explicit-parent-component-call"], [self.name("same_binding")])
        self.assertTrue(all(len(names) == 1 for names in owners.values()))

    def test_current_pending_appendix_and_adjudication_independent_generation(self):
        self.assertEqual(len(self.catalogue["requirements"]), 11)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 57)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 50)
        for requirement in self.catalogue["requirements"]:
            self.assertEqual(requirement["diagnostic_obligation"], "not-required")
            represented = set(generated.ELIGIBLE.get(requirement["id"], []))
            self.assertEqual(set(requirement["pending"]), set(requirement["facets"]) - represented)
        question = next(a for a in self.catalogue["accounting"]
                        if a["unit"] == "p2.b07-additional-parameter-domain")
        self.assertEqual(question["disposition"], "unresolved")
        self.assertEqual(generated.synced_catalogue(self.catalogue, self.specs), self.catalogue)
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue, self.specs))
        native = Registry(ROOT)
        native.catalogues = {"7.5.7.3": self.catalogue}
        native.render()
        appendix = view.split("## Complete finite pending plans\n", 1)[1].split(
            "## Reproduction and remaining gates", 1)[0]
        self.assertEqual(appendix.count("* **`"), 50)
        for requirement in self.catalogue["requirements"]:
            for facet, plan in requirement["pending"].items():
                self.assertIn(f"* **`{facet}`** - {plan}", appendix)
        reviewed = copy.deepcopy(self.catalogue)
        reviewed.update(review_state="reviewed", review_rationale="Synthetic in-memory test, not an approval.")
        registry = Registry(ROOT)
        registry.catalogues["7.5.7.3"] = reviewed
        reviewed["review_fingerprint"] = registry.catalogue_fingerprint("7.5.7.3")
        self.assertEqual(generated.synced_catalogue(reviewed, self.specs), reviewed)
        self.assertIn("Catalogue source review: reviewed.", generated.render_view(reviewed, self.specs))
        reviewed["review_fingerprint"] = "0" * 64
        self.assertIn("Catalogue source review: stale.", generated.render_view(reviewed, self.specs))

    def test_independent_literal_oracles_reject_missing_extra_and_wrong_results(self):
        for variant, rows in EXPECTED.items():
            correct = {label: value for label, _, value in rows}
            spec = self.spec(variant)
            self.assertEqual(generated.model_observations(spec), correct)
            self.assertTrue(generated.accepts(spec, correct))
            self.assertFalse(generated.accepts(spec, {}))
            self.assertFalse(generated.accepts(spec, dict(correct, unexecuted_call=11)))
            for label in correct:
                missing = dict(correct)
                del missing[label]
                self.assertFalse(generated.accepts(spec, missing))
                for wrong in (0, correct[label] - 1, correct[label] + 1):
                    self.assertFalse(generated.accepts(spec, dict(correct, **{label: wrong})))

    def test_overriding_accessibility_and_binding_name_truth_table(self):
        for same_module, parent_public, same_name, renamed_targets in itertools.product((False, True), repeat=4):
            child_name = "work" if same_name else "extra"
            declarations = [
                generated.derived("parent", bindings=[
                    generated.binding("root_target" if renamed_targets else "base_impl", 11,
                                      access="public" if parent_public else "private")]),
                generated.derived("child", "parent", bindings=[
                    generated.binding("leaf_target" if renamed_targets else "child_impl", 22, name=child_name)],
                    module="overriding_provider" if same_module else "unrelated_extension")]
            types = {t["name"]: t for t in declarations}
            is_override = same_name and (parent_public or same_module)
            self.assertEqual(generated.binding_identity(types, "child", child_name),
                             ("parent", "work") if is_override else ("child", child_name))
            owner, item = generated.resolve_binding(types, "parent", "child", "work", "overriding_provider")
            self.assertEqual(owner, "child" if is_override else "parent")
            self.assertEqual(item["result"], 22 if is_override else 11)

    def test_private_homonym_keeps_distinct_identity_without_pass_parity(self):
        types = self.spec("private_homonym")["types"]
        self.assertNotEqual(generated.binding_identity(types, "parent", "work"),
                            generated.binding_identity(types, "child", "work"))
        self.assertTrue(types["parent"]["bindings"][0]["passed"])
        self.assertFalse(types["child"]["bindings"][0]["passed"])
        self.assertEqual(generated.resolve_binding(types, "parent", "child", "work", "overriding_provider")[0],
                         "parent")
        self.assertEqual(generated.resolve_binding(types, "child", "child", "work", "client")[0], "child")
        with self.assertRaisesRegex(ValueError, "no accessible"):
            generated.visible_binding(types, "parent", "work", "client")
        accessible = self.spec("accessible_private")["types"]
        self.assertEqual(generated.binding_identity(accessible, "child", "work"), ("parent", "work"))
        self.assertEqual(generated.resolve_binding(accessible, "parent", "child", "work",
                                                   "overriding_provider")[0], "child")

    def test_all_two_generation_override_inherit_truth_models(self):
        for first_override, second_override in itertools.product((False, True), repeat=2):
            nodes = [
                generated.derived("root", bindings=[generated.binding("root_work", 11)]),
                generated.derived("middle", "root", bindings=(
                    [generated.binding("middle_work", 22)] if first_override else [])),
                generated.derived("leaf", "middle", bindings=(
                    [generated.binding("leaf_work", 33)] if second_override else []))]
            types = {t["name"]: t for t in nodes}
            expected_owner = "leaf" if second_override else "middle" if first_override else "root"
            expected_value = 33 if second_override else 22 if first_override else 11
            owner, item = generated.resolve_binding(types, "root", "leaf", "work", "client")
            self.assertEqual((owner, item["result"]), (expected_owner, expected_value))
            self.assertEqual(generated.binding_identity(types, owner, "work"), ("root", "work"))
            self.assertEqual(generated.resolve_binding(types, "middle", "middle", "work", "client")[1]["result"],
                             22 if first_override else 11)
            self.assertEqual(generated.resolve_binding(types, "root", "root", "work", "client")[1]["result"], 11)
            with self.assertRaisesRegex(ValueError, "outside"):
                generated.resolve_binding(types, "leaf", "root", "work", "client")

    def test_wrong_static_name_only_and_skipped_generation_countermodels(self):
        faults = {
            "same_binding": {"child-helper": 11, "explicit-parent": 22},
            "different_binding": {"inherited-direct": 33, "inherited-helper": 33},
            "private_homonym": {"private-child-helper": 9},
            "accessible_private": {"overridden-child-helper": 11},
            "override_then_inherit": {"grand-helper": 11, "grand-direct": 11},
            "inherit_then_override": {"leaf-helper": 11, "explicit-middle": 33},
        }
        for variant, changes in faults.items():
            correct = {label: value for label, _, value in EXPECTED[variant]}
            for label, wrong in changes.items():
                self.assertFalse(generated.accepts(self.spec(variant), dict(correct, **{label: wrong})))
            mutated = copy.deepcopy(self.spec(variant))
            for t in mutated["types"].values():
                for item in t["bindings"]:
                    item["result"] = 11
            self.assertFalse(generated.accepts(mutated, generated.model_observations(mutated)))

    def verify_source(self, variant, source):
        modules = re.findall(r"(?ms)^module (\w+)\n(.*?)^end module \1\n", source)
        parsed_types, functions = {}, {}
        for module, body in modules:
            for attributes, name, type_body in re.findall(
                    r"(?ms)^type, public([^:\n]*) :: (\w+)\n(.*?)^end type \2\n", body):
                parent = re.fullmatch(r", extends\((\w+)\)", attributes) if attributes else None
                self.assertTrue(not attributes or parent is not None)
                fields = re.findall(r"(?m)^integer :: (\w+)$", type_body)
                bindings = re.findall(r"(?m)^procedure, (public|private)(, nopass)? :: (\w+) => (\w+)$", type_body)
                self.assertEqual(type_body.count("procedure"), len(bindings))
                parsed_types[name] = (parent[1] if parent else None, fields, module, bindings)
            for name, arguments, body in re.findall(
                    r"(?ms)^integer function (\w+)\(([^)]*)\) result\(value\)\n(.*?)^end function \1\n", body):
                self.assertNotIn(name, functions)
                functions[name] = (arguments, body)
        self.assertEqual({name: (row[0], row[1]) for name, row in parsed_types.items()}, SHAPES[variant])
        for name, (_, _, module, _) in parsed_types.items():
            self.assertEqual(module, "unrelated_extension" if variant == "private_homonym" and name == "child"
                             else "overriding_provider")
        helper_type = "root" if variant in ("override_then_inherit", "inherit_then_override") else "parent"
        self.assertEqual(functions.pop("dispatch"),
                         ("self", f"class({helper_type}), intent(in) :: self\nvalue=self%work()\n"))
        targets = {"parent_work": 7 if variant == "private_homonym" else 11,
                   "root_work": 11, "child_work": 22, "child_extra": 33, "leaf_work": 33, "foreign_work": 9}
        seen = set()
        for owner, (_, _, _, bindings) in parsed_types.items():
            for access, nopass, name, target in bindings:
                seen.add(target)
                self.assertEqual(name, "extra" if target == "child_extra" else "work")
                self.assertEqual(access, "private" if owner == "parent" and variant in
                                 ("private_homonym", "accessible_private") else "public")
                self.assertEqual(bool(nopass), target == "foreign_work")
                arguments, body = functions[target]
                expected_fields = []
                ancestor = owner
                while ancestor is not None:
                    expected_fields = parsed_types[ancestor][1] + expected_fields
                    ancestor = parsed_types[ancestor][0]
                if nopass:
                    self.assertEqual(arguments, "")
                    self.assertEqual(body, "value=9\n")
                else:
                    self.assertEqual(arguments, "self")
                    self.assertTrue(body.startswith(f"class({owner}), intent(in) :: self\n"))
                    guards = re.findall(r"(?m)^if \(self%(\w+) /= (\d+)\) error stop \d+$", body)
                    self.assertEqual([(field, int(value)) for field, value in guards],
                                     [(field, FIELDS[field]) for field in expected_fields])
                    remaining = body.split("\n", 1)[1]
                    remaining = re.sub(r"(?m)^if \(self%\w+ /= \d+\) error stop \d+\n", "", remaining)
                    self.assertEqual(remaining, f"value={targets[target]}\n")
        self.assertEqual(set(functions), seen)
        main = source.split("program p\n", 1)[1].split("contains\n", 1)[0]
        actual_calls = [(label, expression, int(value)) for label, expression, value in re.findall(
            r"(?m)^call expect_value\('([^']+)',(.+),(\d+)\)$", main)]
        self.assertEqual(actual_calls, EXPECTED[variant])
        assignments = {target: int(value) for target, value in re.findall(r"(?m)^(\w+(?:%\w+)+)=(\d+)$", main)}
        self.assertEqual(assignments, self.spec(variant)["setup"])
        declared = dict(re.findall(r"(?m)^type\((\w+)\) :: (\w+)$", main))
        self.assertEqual({variable: typename for typename, variable in declared.items()}, self.spec(variant)["variables"])
        for typename, variable in declared.items():
            target = variable
            owner = typename
            while owner is not None:
                parent, fields, _, _ = parsed_types[owner]
                for field in fields:
                    self.assertEqual(assignments[target + "%" + field], FIELDS[field])
                owner = parent
                if parent is not None:
                    target += "%" + parent
        self.assertLess(max(main.index(target + "=") for target in assignments), main.index("call expect_value"))
        self.assertIn("contains\n" + generated.OBSERVER + "end program p\n", source)
        self.assertIn("if (actual /= expected) then\n", generated.OBSERVER)
        self.assertIn("error stop 1\nend if", generated.OBSERVER)

    def test_actual_program_interfaces_definitions_scopes_and_literal_guards(self):
        for variant in EXPECTED:
            with self.subTest(variant=variant):
                self.verify_source(variant, self.source(variant))

    def test_actual_program_guards_reject_setup_observer_and_dispatch_mutations(self):
        source = self.source("same_binding")
        mutations = [
            source.replace("value=self%work()", "value=22"),
            source.replace("value=22", "value=11"),
            source.replace("if (self%child_token /= 29) error stop 102\n", ""),
            source.replace("extended%parent%parent_token=17", "extended%parent%parent_token=29"),
            source.replace("call expect_value('child-helper',dispatch(extended),22)\n", ""),
            source.replace("if (actual /= expected) then", "if (actual == expected) then"),
        ]
        for mutated in mutations:
            self.assertNotEqual(mutated, source)
            with self.assertRaises(AssertionError):
                self.verify_source("same_binding", mutated)
        source = self.source("private_homonym")
        with self.assertRaises(AssertionError):
            self.verify_source("private_homonym", source.replace("procedure, public, nopass :: work",
                                                                "procedure, public :: work"))

    def test_no_abstract_parameter_pointer_generic_or_external_private_shortcuts(self):
        forbidden = (r"\babstract\b", r"\bsequence\b", r"\bbind\s*\(", r"\bdeferred\b", r"\bnon_overridable\b",
                     r"\bgeneric\b", r"\bfinal\b", r"\bpointer\b", r"\ballocatable\b", r"\bvalue\s*::",
                     r"\bselect\s+type\b", r"\bsame_type_as\b", r"\bextends_type_of\b", r"\bc_loc\b",
                     r"\bpure\b", r"\bsimple\b", r"\belemental\b")
        for variant in EXPECTED:
            source = self.source(variant)
            for expression in forbidden:
                self.assertNotRegex(source.lower(), expression)
            main = source.split("program p\n", 1)[1].split("contains\n", 1)[0]
            for variable in self.spec(variant)["variables"]:
                self.assertNotRegex(main, rf"(?m)^{variable}\s*=")
            if variant in ("private_homonym", "accessible_private"):
                self.assertNotIn("base%work()", main)
                self.assertNotIn("extended%parent%work()", main)

    def test_shared_parameter_helper_inputs_remain_exact(self):
        corpus = parameters.build_corpus()
        self.assertEqual((len(corpus.cases), len(corpus.files)), (66, 105))
        self.assertFalse(set(corpus.files) & set(self.outputs))
        for path, content in corpus.files.items():
            self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
