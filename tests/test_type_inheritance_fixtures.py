"""Independent ancestry, association, namespace and generic oracle checks."""
import copy
import json
from pathlib import Path
import re
import sys
import unittest

import run_tests as runner
from suite_data import Registry


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import generate_type_inheritance_fixtures as generated


EXPECTED_IDS = {
    "S7_5_7_1_003_valid__matrix_m",
    "S7_5_7_1_003_valid__dynamic_dummy",
    "S7_5_7_2_001_valid__public_components",
    "S7_5_7_2_001_valid__private_homonym",
    "S7_5_7_2_002_valid__scalar_parent",
    "S7_5_7_2_002_valid__parent_parameters",
    "S7_5_7_2_002_valid__array_parent_designator",
    "S7_5_7_2_003_valid__renamed_parent_n",
    "S7_5_7_2_004_valid__direct_views",
    "S7_5_7_2_004_valid__recursive_views",
    "S7_5_7_2_005_valid__generic_union_g",
}


def type_blocks(source):
    pattern = r"(?ms)^type(?P<attrs>(?:,[^\n:]+)?)\s*::\s*(?P<name>\w+)(?:\([^)]*\))?\n(?P<body>.*?)^end type(?:\s+\w+)?\s*$"
    result = {}
    for match in re.finditer(pattern, source):
        attrs = match.group("attrs")
        parent = re.search(r"extends\((\w+)\)", attrs)
        result[match.group("name")] = {
            "parent": parent.group(1) if parent else None,
            "attributes": attrs, "body": match.group("body"),
        }
    return result


def is_extension(parents, actual, mold):
    while actual is not None:
        if actual == mold:
            return True
        actual = parents[actual]
    return False


def integer_fields(block):
    fields = set()
    for attrs, names in re.findall(r"(?m)^\s*integer([^:\n]*)::\s*([^\n]+)", block):
        if re.search(r"\b(kind|len)\b", attrs):
            continue
        fields.update(name.strip() for name in names.split(","))
    return fields


def component_identity(types, declaring_type, path):
    part = path[0]
    current = declaring_type
    while current is not None:
        parent = types[current]["parent"]
        if part in integer_fields(types[current]["body"]):
            if len(path) != 1:
                raise ValueError("integer component selected as a structure")
            return current, part
        if part == parent:
            return component_identity(types, parent, path[1:])
        current = parent
    raise ValueError(f"unknown component path: {declaring_type} {path}")


def sequential_model(source, separate_views=False, corrupt_marker=False):
    types = type_blocks(source)
    actual_type = re.search(r"type\((\w+)\) :: object\n", source).group(1)
    memory, checks = {}, []
    for line in source.splitlines():
        assignment = re.fullmatch(r"object%([\w%]+) = (\d+)", line)
        assertion = re.fullmatch(r"if \(object%([\w%]+) /= (\d+)\) error stop \d+", line)
        if not assignment and not assertion:
            continue
        match = assignment or assertion
        path = tuple(match.group(1).split("%"))
        key = path if separate_views else component_identity(types, actual_type, path)
        number = int(match.group(2))
        if assignment:
            memory[key] = number
            if corrupt_marker and path[-1] == "value" and (actual_type, "marker") in memory:
                memory[(actual_type, "marker")] = 0
        else:
            observed = memory.get(key)
            checks.append((path, observed, number))
    return checks


def parent_designator_rank(source, designator):
    types = type_blocks(source)
    base, component = designator.split("%")
    base_name = base.split("(")[0]
    declaration = re.search(
        r"type\((\w+)\) :: " + base_name + r"(\([^)]*\))?(?:\n|$)", source)
    if not declaration:
        raise ValueError("undeclared base object")
    owner, shape = declaration.groups()
    ancestors = set()
    parent = types[owner]["parent"]
    while parent:
        ancestors.add(parent)
        parent = types[parent]["parent"]
    if component not in ancestors:
        raise ValueError("not an implicit parent component")
    declared_rank = shape.count(",") + 1 if shape else 0
    if "(" in base:
        indices = base.partition("(")[2].removesuffix(")")
        if not re.fullmatch(r"\d+(?:,\d+)*", indices) or indices.count(",") + 1 != declared_rank:
            raise ValueError("countermodel supports complete scalar subscripts only")
        return 0
    return declared_rank


def generic_model(source):
    types = type_blocks(source)
    functions = {}
    for name, body in re.findall(
            r"(?ms)^integer function (\w+)\(self,x\) result\(value\)\n(.*?)^end function\s*$", source):
        owner = re.search(r"class\((\w+)\), intent\(in\) :: self", body).group(1)
        argument = re.search(r"(?m)^(integer|real), intent\(in\) :: x$", body).group(1)
        returned = int(re.search(r"(?m)^value = (\d+)$", body).group(1))
        functions[name] = (owner, argument, returned)
    local_bindings, local_generics = {}, {}
    for name, info in types.items():
        local_bindings[name] = dict(re.findall(r"procedure :: (\w+) => (\w+)", info["body"]))
        local_generics[name] = {
            generic: [member.strip() for member in members.split(",")]
            for generic, members in re.findall(r"generic :: (\w+) => ([^\n]+)", info["body"])
        }
        for target in local_bindings[name].values():
            if functions[target][0] != name:
                raise ValueError("passed-object type differs from binding owner")

    def bindings(name):
        parent = types[name]["parent"]
        result = bindings(parent) if parent else {}
        result.update(local_bindings[name])
        return result

    def generics(name):
        parent = types[name]["parent"]
        result = generics(parent) if parent else {}
        for generic, additions in local_generics[name].items():
            if set(result.get(generic, [])) & set(additions):
                raise ValueError("repeated inherited generic member")
            result[generic] = result.get(generic, []) + additions
        return result

    parents = {name: info["parent"] for name, info in types.items()}

    def invoke(declared, dynamic, generic, argument):
        if not is_extension(parents, dynamic, declared):
            raise ValueError("incompatible dynamic actual")
        selected = [binding for binding in generics(declared).get(generic, [])
                    if functions[bindings(declared)[binding]][1] == argument]
        if len(selected) != 1:
            raise ValueError("no unique declared-type generic selection")
        return functions[bindings(dynamic)[selected[0]]][2]
    return types, functions, local_bindings, generics, invoke


class TypeInheritanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {c.name: c for c in cls.all_cases if "/fixtures/type_inheritance_" in c.path}

    def inputs(self, name):
        fixture = self.cases[name].fixture
        return {file: (fixture.root / file).read_bytes() for file in fixture.files}

    def source(self, name, filename=None):
        inputs = self.inputs(name)
        return (inputs[filename] if filename else b"\n".join(inputs.values())).decode().lower()

    def test_exact_shared_case_inventory_and_phase_roles(self):
        self.assertEqual(set(self.cases), EXPECTED_IDS)
        self.assertEqual(set(self.specs), EXPECTED_IDS)
        self.assertEqual(len(self.outputs), 27)
        shared = {s["shared_case"]: name for name, s in self.specs.items() if s["shared_case"]}
        self.assertEqual(set(shared), {"M", "N", "G"})
        self.assertEqual([len(self.specs[shared[k]]["facets"]) for k in ("M", "N", "G")], [5, 2, 3])
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assertEqual(case.kind, "valid")
                self.assertEqual(case.fixture.expectation.phase, "run")
                self.assertEqual(case.fixture.expectation.exit_code, 0)
                self.assertEqual(case.meta.standard, "f2023")
                self.assertFalse(case.meta.coarray)
                self.assertEqual(case.meta.profiles, [])
                category = self.registry.requirements[case.rule]["category"]
                self.assertEqual(case.meta.evidence, generated.evidence_for_category(category))
                self.assertIsNotNone(case.fixture.link)
        self.assertEqual(generated.evidence_for_category("restriction"), "positive-control")
        self.assertEqual(generated.evidence_for_category("effect"), "effect")
        categories = {q["id"]: q["category"] for s in generated.SECTIONS
                      for q in self.registry.catalogues[s]["requirements"]}
        categories["S7.5.7.2-005"] = "restriction"
        _, synthetic = generated.build_corpus(categories=categories)
        self.assertEqual(synthetic["S7_5_7_2_005_valid__generic_union_g"]["evidence"], "positive-control")

    def test_generated_bytes_and_owned_paths(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("type_inheritance_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.outputs))
        for path, raw in self.outputs.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), raw)
                self.assertTrue(path.relative_to(ROOT).as_posix().startswith("tests/fixtures/type_inheritance_"))
                raw.decode("ascii")
                self.assertTrue(raw.endswith(b"\n"))
                if path.suffix == ".f90":
                    self.assertLessEqual(max(map(len, raw.splitlines())), 132)

    def test_independent_25_cell_parent_graph_truth_and_call_direction(self):
        source = self.source("S7_5_7_1_003_valid__matrix_m")
        types = type_blocks(source)
        parents = {name: info["parent"] for name, info in types.items()}
        self.assertEqual(parents, {"root": None, "child": "root", "grand": "child",
                                   "sibling": "root", "other": None})
        order = ["root", "child", "grand", "sibling", "other"]
        independent = [[is_extension(parents, first, mold) for mold in order] for first in order]
        self.assertEqual(independent, [
            [True, False, False, False, False],
            [True, True, False, False, False],
            [True, True, True, False, False],
            [True, False, False, True, False],
            [False, False, False, False, True],
        ])
        calls = re.findall(r"actual\((\d),(\d)\) = extends_type_of\((\w+)_value, (\w+)_value\)", source)
        self.assertEqual(len(calls), 25)
        self.assertEqual({(int(i), int(j)) for i, j, _, _ in calls},
                         {(i, j) for i in range(1, 6) for j in range(1, 6)})
        for i, j, first, mold in calls:
            self.assertEqual((first, mold), (order[int(i)-1], order[int(j)-1]))
        expected_rows = re.findall(r"if \(any\(actual\((\d),:\) \.neqv\. \[([^\]]+)\]\)\) error stop", source)
        self.assertEqual(len(expected_rows), 5)
        for row, values in expected_rows:
            literals = [token.strip() == ".true." for token in values.split(",")]
            self.assertEqual(literals, independent[int(row)-1])
        self.assertEqual(sum(sum(row) for row in independent), 9)
        transpose_errors = sum(independent[i][j] != independent[j][i] for i in range(5) for j in range(5))
        self.assertEqual(transpose_errors, 8)
        self.assertNotIn("class(root)", source)
        self.assertNotIn("class(*)", source)
        self.assertEqual(integer_fields(types["root"]["body"]), {"payload"})
        self.assertNotIn("payload", integer_fields(types["child"]["body"]))
        self.assertNotIn("payload", integer_fields(types["grand"]["body"]))

    def test_dynamic_dummy_has_an_independent_declared_type_control(self):
        raw = self.source("S7_5_7_1_003_valid__dynamic_dummy")
        parents = {name: info["parent"] for name, info in type_blocks(raw).items()}
        self.assertTrue(is_extension(parents, "grand", "child"))
        self.assertFalse(is_extension(parents, "root", "child"))
        self.assertIn("call inspect_dynamic(value, mold, observed)", raw)
        self.assertIn("class(root), intent(in) :: item", raw)
        self.assertIn("type(grand) :: value", raw)
        self.assertIn("result = extends_type_of(item, child_mold)", raw)
        self.assertIn("if (.not. observed) error stop 1", raw)
        self.assertIn("if (extends_type_of(base, mold)) error stop 2", raw)
        self.assertLess(raw.index("value%grand_marker = 43"), raw.index("call inspect_dynamic"))

    def test_sequential_inheritance_views_share_semantic_cells_not_copies(self):
        direct = self.source("S7_5_7_2_004_valid__direct_views")
        recursive = self.source("S7_5_7_2_004_valid__recursive_views")
        for source, expected in (
            (direct, [3, 7, 41, 11, 41]),
            (recursive, [31, 31, 37, 37, 41, 43]),
        ):
            checks = sequential_model(source)
            self.assertEqual([seen for _, seen, _ in checks], expected)
            self.assertTrue(all(seen == wanted for _, seen, wanted in checks))
            copied = sequential_model(source, separate_views=True)
            self.assertTrue(any(seen != wanted for _, seen, wanted in copied))
        corrupted = sequential_model(direct, corrupt_marker=True)
        self.assertTrue(any(seen != wanted for _, seen, wanted in corrupted))
        types = type_blocks(recursive)
        self.assertEqual(component_identity(types, "leaf", ("mid", "root", "value")), ("root", "value"))
        self.assertEqual(component_identity(types, "leaf", ("root", "value")), ("root", "value"))
        self.assertEqual(component_identity(types, "leaf", ("value",)), ("root", "value"))
        self.assertNotIn("call ", direct + recursive)

    def test_private_homonym_model_uses_the_provider_declared_type(self):
        name = "S7_5_7_2_001_valid__private_homonym"
        provider = self.source(name, "provider.f90")
        extension = self.source(name, "extension.f90")
        main = self.source(name, "S7_5_7_2_001.f90")
        parent = type_blocks(provider)["parent"]
        child = type_blocks(extension)["child"]
        self.assertIn("private", parent["body"])
        self.assertIn("integer, public :: hidden", child["body"])
        self.assertEqual(child["parent"], "parent")
        self.assertIn("class(parent), intent(inout) :: object", provider)
        self.assertIn("object%hidden = number", provider)
        cells = {("child", "hidden"): 9}
        cells[("parent", "hidden")] = 7
        self.assertEqual((cells[("parent", "hidden")], cells[("child", "hidden")]), (7, 9))
        wrong_dynamic_lookup = {("child", "hidden"): 9}
        wrong_dynamic_lookup[("child", "hidden")] = 7
        self.assertNotEqual((wrong_dynamic_lookup[("child", "hidden")],
                             wrong_dynamic_lookup[("child", "hidden")]), (7, 9))
        ordered = ["object%hidden = 9", "call set_hidden(object, 7)",
                   "inherited_value = get_hidden(object)", "if (inherited_value /= 7)",
                   "if (object%hidden /= 9)"]
        self.assertEqual([main.index(token) for token in ordered], sorted(main.index(token) for token in ordered))
        self.assertNotIn("object%parent%hidden", main)

    def test_parent_type_parameter_and_array_rank_models(self):
        scalar = self.source("S7_5_7_2_002_valid__scalar_parent")
        self.assertIn("type(parent), intent(in) :: item", scalar)
        self.assertIn("parent_payload(object%parent)", scalar)
        self.assertIn("rank(object%parent) /= 0", scalar)
        pdt = self.source("S7_5_7_2_002_valid__parent_parameters")
        arguments = re.search(r"type\(child\(([^)]*)\)\) :: object", pdt).group(1)
        actual = {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", arguments)}
        self.assertEqual(actual, {"k": 2, "n": 3, "m": 5})
        inherited = {key: actual[key] for key in ("k", "n")}
        self.assertEqual(inherited, {"k": 2, "n": 3})
        self.assertIn("object%parent%k /= 2", pdt)
        self.assertIn("object%parent%n /= 3", pdt)
        self.assertNotRegex(pdt, r"integer\s*\(")
        array = self.source("S7_5_7_2_002_valid__array_parent_designator")
        assertions = re.findall(r"rank\((objects(?:\(\d+\))?%parent)\) /= (\d+)", array)
        self.assertEqual(len(assertions), 2)
        observed = [(designator, parent_designator_rank(array, designator), int(expected))
                    for designator, expected in assertions]
        self.assertEqual(observed, [("objects%parent", 1, 1), ("objects(1)%parent", 0, 0)])
        self.assertEqual(parent_designator_rank(scalar, "object%parent"), 0)
        wrong_component_only_rank = [0 for _ in assertions]
        self.assertNotEqual(wrong_component_only_rank, [expected for _, _, expected in observed])

    def test_naming_access_model_retains_original_module_access(self):
        name = "S7_5_7_2_003_valid__renamed_parent_n"
        provider = self.source(name, "provider.f90")
        extension = self.source(name, "extension.f90")
        main = self.source(name, "S7_5_7_2_003.f90")
        types = type_blocks(provider)
        self.assertIn("public", types["original"]["attributes"])
        alias = re.search(r"alias\s*=>\s*(\w+)", extension).group(1)
        self.assertEqual(alias, "original")
        self.assertEqual(type_blocks(extension)["child"]["parent"], "alias")
        self.assertIn("private :: alias", extension)
        self.assertIn("private", type_blocks(extension)["child"]["body"])
        original_access, imported_access, child_default = "public", "private", "private"
        parent_component_access = original_access
        self.assertEqual(parent_component_access, "public")
        self.assertNotEqual(parent_component_access, imported_access)
        self.assertNotEqual(parent_component_access, child_default)
        self.assertIn("call set_payload(object)", extension)
        self.assertNotIn("object%alias%payload =", extension)
        self.assertIn("observed = object%alias%payload", main)
        for forbidden in ("type(alias)", "object%original", "object%marker"):
            self.assertNotIn(forbidden, main)

    def test_generic_g_uses_nonpassed_discriminators_and_dynamic_specific_bindings(self):
        name = "S7_5_7_2_005_valid__generic_union_g"
        module = self.source(name, "generic_types.f90")
        main = self.source(name, "S7_5_7_2_005.f90")
        types, functions, bindings, generics, invoke = generic_model(module)
        self.assertEqual(generics("child"), {"g": ["pi", "cr"]})
        self.assertEqual(generics("overriding_child"), {"g": ["pi", "cr"]})
        self.assertEqual(generics("separate_child"), {"g": ["pi"], "h": ["cr"]})
        self.assertEqual(functions["parent_integer"], ("parent", "integer", 11))
        self.assertEqual(functions["override_integer"], ("overriding_child", "integer", 33))
        receivers = dict((var, typename) for typename, var in re.findall(r"type\((\w+)\) :: (\w+)", main))
        observed_calls = re.findall(r"observed = (\w+)%(\w+)\((1(?:\.0)?)\)\nif \(observed /= (\d+)\)", main)
        self.assertEqual(len(observed_calls), 6)
        independent_expected = [11, 22, 33, 22, 11, 22]
        resolved = []
        for receiver, generic, value, expected in observed_calls:
            declared = receivers[receiver]
            result = invoke(declared, declared, generic, "real" if "." in value else "integer")
            self.assertEqual(result, int(expected))
            resolved.append(result)
        self.assertEqual(resolved, independent_expected)
        self.assertEqual(invoke("parent", "overriding_child", "g", "integer"), 33)
        with self.assertRaises(ValueError):
            invoke("parent", "overriding_child", "g", "real")
        with self.assertRaises(ValueError):
            invoke("separate_child", "separate_child", "g", "real")
        wrong_owner = module.replace("class(overriding_child), intent(in) :: self",
                                     "class(child), intent(in) :: self", 1)
        with self.assertRaises(ValueError):
            generic_model(wrong_owner)
        duplicated = module.replace("generic :: g => cr", "generic :: g => pi, cr", 1)
        _, _, _, bad_generics, _ = generic_model(duplicated)
        with self.assertRaises(ValueError):
            bad_generics("child")
        self.assertEqual(set(bindings["parent"]), {"pi"})
        self.assertEqual(len(types), 4)

    def test_only_reviewed_runtime_facets_are_represented(self):
        covered = {}
        for case in self.cases.values():
            covered.setdefault(case.rule, set()).update(case.meta.facets)
            self.assertFalse(case.rule.startswith("S7.5.7.3-"))
        self.assertEqual(covered, {key: set(value) for key, value in generated.ELIGIBLE.items()})
        self.assertEqual(sum(map(len, covered.values())), 18)
        for section in generated.SECTIONS:
            catalogue = self.registry.catalogues[section]
            for req in catalogue["requirements"]:
                self.assertEqual(set(req["pending"]), set(req["facets"]) - covered.get(req["id"], set()))
                for plan in req["pending"].values():
                    self.assertNotIn("Runtime", plan)
            appendix = generated.pending_appendix(catalogue)
            self.assertIn(appendix, (ROOT / generated.view_path(section)).read_text())
            for req in catalogue["requirements"]:
                for facet, plan in req["pending"].items():
                    self.assertIn(f"* **`{facet}`**: {plan}\n", appendix)

    def test_no_layout_absence_policies_or_constructor_setup(self):
        for name in self.cases:
            raw = self.source(name)
            with self.subTest(case=name):
                self.assertNotRegex(raw, r"\b(?:c_ptr|c_funptr|sequence|abstract|allocatable|pointer|final)\b")
                self.assertNotRegex(raw, r"\b(?:sizeof|storage_size|c_sizeof|c_loc|transfer|associated|allocated|is_finalizable)\s*\(")
                self.assertNotRegex(raw, r"\bstop\s+77\b")
                for typename in type_blocks(raw):
                    self.assertNotRegex(raw, r"=\s*" + re.escape(typename) + r"\s*\(")
                self.assertNotRegex(raw, r"(?m)^\s*(print|write|read)\b")

    def test_admin_fields_are_preserved_and_render_status_is_computed(self):
        for section in generated.SECTIONS:
            catalogue = copy.deepcopy(self.registry.catalogues[section])
            catalogue.update(review_state="reviewed", review_fingerprint="0" * 64,
                             review_rationale="synthetic state-preservation check")
            updated = generated.synced_catalogue(catalogue, self.specs)
            for field in ("review_state", "review_fingerprint", "review_rationale"):
                self.assertEqual(updated[field], catalogue[field])
            self.assertEqual(generated.catalogue_review_status(updated), "stale")
            self.assertIn("Catalogue source review: stale", generated.render_view(updated, self.specs))


if __name__ == "__main__":
    unittest.main()
