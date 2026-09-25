"""Bounded source isolation and causal-report countermodels for constructor declarations."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry

sys.path.insert(0, str(ROOT / "tools"))
import generate_constructor_declaration_fixtures as generated
import generate_structure_constructor_effect_fixtures as runtime_generated
import generate_structure_constructor_7_5_10_b_fixtures as batch317_generated


PAIRS = {
    "C7101": ["abstract"],
    "C7102": ["repeated_keyword", "positional_repeat"],
    "C7103": ["ancestor_overlap"],
    "C7104": ["missing_ordinary", "missing_pointer"],
    "C7105": ["keyword_order"],
    "C7106": ["unknown_keyword", "parameter_keyword"],
    "C7109": ["procedure_in_data", "data_in_procedure"],
    "C7110": ["array_to_scalar", "scalar_to_array"],
}
WRONG_CAUSES = {
    "C7101": [
        "Cannot declare variable 'self' of ABSTRACT type 'base'",
        "Abstract type 'base' has an unimplemented deferred binding",
        "Cannot construct ABSTRACT type 'other'",
    ],
    "C7102": [
        "Component 'right' is initialized twice in the structure constructor",
        "Type parameter 'left' is initialized twice in the structure constructor",
        "No initializer for component 'right' given in the structure constructor",
        "Component 'left' has the wrong type in the structure constructor",
    ],
    "C7103": [
        "Component 'x' is initialized twice in the structure constructor",
        "Component 'y' conflicts with parent component 'parent'",
        "Component 'x' is inaccessible in parent component 'parent'",
        "No initializer for component 'z' given in the structure constructor",
    ],
    "C7104": [
        "No initializer for component 'other' given in the structure constructor",
        "Missing actual argument 'right' in call to function 'pair'",
        "Component 'right' is inaccessible in the structure constructor",
        "Pointer component 'p' has a rank mismatch in the structure constructor",
    ],
    "C7105": [
        "Missing keyword name in actual argument list",
        "A positional argument follows a keyword argument in function call 'pair'",
        "A positional type parameter follows a keyword in derived type specifier 'pair'",
        "Component 'left' is initialized twice in the structure constructor",
        "Structure constructor lacks a value for component 'right'",
        "A positional component follows a keyword component in structure constructor 'other'",
    ],
    "C7106": [
        "Unknown dummy keyword 'extra' in call to function 'packet'",
        "Type parameter 'k' is not a constant expression",
        "Type parameter 'k' has an unsupported kind value",
        "Unknown component keyword 'other' in constructor 'packet'",
        "Unknown component keyword 'extra' in constructor 'other'",
        "Component 'k' is initialized twice in the structure constructor",
    ],
    "C7109": [
        "Procedure 'worker' has an incompatible explicit interface for component 'action'",
        "Procedure pointer component 'action' requires the NOPASS attribute",
        "Data target 'datum' lacks the TARGET attribute",
        "Procedure target 'other' cannot initialize data pointer component 'p'",
        "Data target 'datum' cannot initialize procedure pointer component 'other'",
        "The element in the structure constructor at (1), for pointer component 'p' should be a POINTER or a TARGET",
    ],
    "C7110": [
        "Data target 'vec' lacks the TARGET attribute for component 'one'",
        "Pointer component 'many' has the wrong kind, expected INTEGER",
        "NULL must not have a MOLD argument in a structure constructor",
        "Data target 'vec' has rank 2 but pointer component 'one' has rank 0",
        "Data target 'scalar_target' has rank 0 but pointer component 'many' has rank 2",
        "Rank mismatch in ordinary value assignment (1/0)",
    ],
}


def split_items(value):
    result, start, depth = [], 0, 0
    for i, char in enumerate(value):
        if char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif char == "," and depth == 0:
            result.append(value[start:i].strip())
            start = i + 1
    if value[start:].strip():
        result.append(value[start:].strip())
    return result


def group_at(value, start):
    assert value[start] == "("
    depth = 0
    for i in range(start, len(value)):
        if value[i] == "(":
            depth += 1
        elif value[i] == ")":
            depth -= 1
            if depth == 0:
                return value[start+1:i], i + 1
    raise AssertionError("unbalanced finite source")


def type_model(source):
    result = {}
    pattern = r"(?ms)^type(?P<attrs>,[^\n:]*)?\s*::\s*(?P<name>\w+)(?:\((?P<params>[^)]*)\))?\n(?P<body>.*?)^end type[^\n]*"
    for match in re.finditer(pattern, source):
        attrs = match["attrs"] or ""
        parent = re.search(r"extends\((\w+)\)", attrs)
        fields, order = {}, []
        if parent:
            fields.update(copy.deepcopy(result[parent[1]]["fields"]))
            order.extend(result[parent[1]]["order"])
            fields[parent[1]] = dict(category="ancestor", rank=0, default=False)
        parameters = []
        for line in match["body"].splitlines():
            if line.startswith("integer, kind"):
                parameters.append(line.split("::")[1].strip())
                continue
            declaration = re.match(r"^(integer(?:,[^:]*)?|procedure\([^)]*\),[^:]*)\s*::\s*(\w+)(\([^)]*\))?(.*)$", line)
            if not declaration:
                continue
            attributes, name, dimensions, initial = declaration.groups()
            category = "procedure" if attributes.startswith("procedure") else (
                "pointer" if "pointer" in attributes else "value")
            fields[name] = dict(category=category, rank=1 if dimensions else 0, default="=" in initial)
            order.append(name)
        result[match["name"]] = dict(
            fields=fields, order=order, parameters=parameters,
            abstract="abstract" in attrs, parent=parent[1] if parent else None,
        )
    return result


def target_model(source):
    result = {}
    main = source.split("program constructor_case\n", 1)[1]
    for match in re.finditer(r"(?m)^integer,\s*(target|pointer)\s*::\s*([^\n]+)", main):
        for item in split_items(match[2]):
            name = re.match(r"(\w+)(\([^)]*\))?", item)
            result[name[1]] = 1 if name[2] else 0
    return result


def constructor_faults(source, line, name):
    """Finite source bookkeeping, not an interpretation of invalid Fortran execution."""
    model = type_model(source)
    definition = model[name]
    fields, order = definition["fields"], definition["order"]
    start = line.index(name + "(") + len(name)
    arguments, end = group_at(line, start)
    if end < len(line) and line[end] == "(":
        arguments, end = group_at(line, end)
    supplied, values, faults = [], {}, set()
    saw_keyword = False
    if definition["abstract"]:
        faults.add("C7101")
    for index, item in enumerate(split_items(arguments)):
        keyword = re.match(r"^(\w+)=(?!=|>)(.*)$", item)
        if keyword:
            component, value = keyword.groups()
            saw_keyword = True
        else:
            if saw_keyword:
                faults.add("C7105")
            # Nominal list position isolates C7105 without defining its invalid runtime meaning.
            component, value = order[index], item
        if component not in fields:
            faults.add("C7106")
            continue
        if component in supplied:
            faults.add("C7102")
        supplied.append(component)
        values[component] = value
    parent = definition["parent"]
    covered = set(supplied)
    if parent and parent in supplied:
        inherited = set(model[parent]["fields"])
        if inherited & set(supplied):
            faults.add("C7103")
        covered |= inherited
    for component, field in fields.items():
        if field["category"] != "ancestor" and component not in covered and not field["default"]:
            faults.add("C7104")
    targets = target_model(source)
    implementation = re.sub(r"(?s)abstract interface\n.*?end interface\n", "", source)
    procedures = set(re.findall(r"(?m)^subroutine (\w+)\(", implementation))
    for component, value in values.items():
        field = fields[component]
        if field["category"] == "pointer":
            if value in procedures:
                faults.add("C7109")
                continue
            if value.startswith("null("):
                mold = re.search(r"mold=(\w+)", value)
                rank = targets[mold[1]] if mold else field["rank"]
            else:
                target = re.match(r"(\w+)(?:\(([^)]*)\))?$", value)
                if not target or target[1] not in targets:
                    faults.add("target-eligibility")
                    continue
                rank = targets[target[1]] if not target[2] or ":" in target[2] else 0
            if rank != field["rank"]:
                faults.add("C7110")
        elif field["category"] == "procedure" and value not in procedures and not value.startswith("null("):
            faults.add("C7109")
    return faults


class ConstructorDeclarationFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs, cls.repairs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {c.name: c for c in all_cases if "/fixtures/constructor_declaration_" in c.path}
        cls.legacy = {c.name: c for c in all_cases if c.name in generated.LEGACY_IDS}
        cls.catalogue = cls.registry.catalogues["7.5.10"]

    def source(self, name):
        case = self.cases[name]
        return (case.fixture.root / self.specs[name]["source_file"]).read_text()

    def judge(self, name, message, family="lfortran", code=1, filename=None, line=None,
              severity="error", timed_out=False, suffix="", echo=False, predicate=None):
        case = self.cases[name]
        condition = predicate or case.fixture.expectation.diagnostic
        filename = filename or condition["file"]
        line = condition["line"] if line is None else line
        location = f"{line}-{line}:1-120" if family == "lfortran" else f"{line}:1"
        heading = "semantic error" if family == "lfortran" and severity == "error" else severity
        output = f"{filename}:{location}: {heading}: {'unrelated failure' if echo else message}\n"
        if echo:
            output += "  1 | " + message + "\n"
        output += suffix
        return runner.judge_diagnostic(
            runner.ProcessResult(code, output, timed_out=timed_out),
            runner.Compiler(family, family, "f23" if family == "lfortran" else "f2023"),
            case.rule, condition)

    def test_exact_case_ids_roles_phases_and_no_runtime_plan(self):
        expected = {generated.identifier(rule, variant, invalid)
                    for rule, variants in PAIRS.items() for variant in variants
                    for invalid, variant in [(True, variant), (False, variant + "_repair")]}
        expected |= {generated.identifier("R756", "empty_components"),
                     generated.identifier("S7.5.10-006", "prior_definition")}
        self.assertEqual(len(expected), 28)
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.specs), expected)
        self.assertEqual(len(self.repairs), 13)
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assertEqual(case.fixture.expectation.phase, "compile")
                self.assertEqual(case.meta.evidence, "effect" if case.kind == "invalid" else "positive-control")
                self.assertEqual(case.fixture.expectation.outcome, "diagnose" if case.kind == "invalid" else "success")
                self.assertEqual(case.meta.standard, "f2023")
                self.assertEqual(case.meta.oracle_basis, "standard")
                self.assertEqual(case.meta.images, 1)
                self.assertFalse(case.meta.profiles)
                self.assertFalse(case.meta.coarray)
                self.assertFalse(case.fixture.link)
                self.assertNotRegex(self.source(name), r"(?i)\b(?:print|error stop|deallocate|allocate)\b")
                self.assertNotRegex(self.source(name), r"(?i)\b(?:associated|lbound|ubound|size|rank)\s*\(")
        s = self.cases[generated.identifier("S7.5.10-006", "prior_definition")]
        self.assertEqual(s.meta.evidence, "positive-control")
        self.assertEqual(self.registry.requirements[s.rule]["category"], "restriction")
        self.assertEqual(self.registry.requirements[s.rule]["diagnostic_obligation"], "not-required")

    def test_generated_bytes_and_scoped_paths(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("constructor_declaration_*/*") if p.is_file()}
        self.assertEqual(actual, set(self.outputs))
        self.assertEqual(len(actual), 56)
        for path, content in self.outputs.items():
            self.assertEqual(path.read_bytes(), content)
            content.decode("ascii")
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, content.splitlines())), 132)
        for name, spec in self.specs.items():
            self.assertEqual(spec["source_file"], generated.source_name(spec["rule"]))

    def test_minimal_same_primary_repairs_and_source_fault_isolation(self):
        for name, repair in self.repairs.items():
            bad, good = self.source(name), self.source(repair["control"])
            case = self.cases[name]
            with self.subTest(case=name):
                self.assertEqual(bad.count(repair["wrong"]), 1)
                self.assertEqual(bad.replace(repair["wrong"], repair["repaired"], 1), good)
                self.assertEqual(case.rule, self.cases[repair["control"]].rule)
                self.assertEqual(case.fixture.expectation.diagnostic["file"], repair["file"])
                self.assertEqual(bad.splitlines()[repair["line"]-1], repair["anchor"])
                self.assertEqual(case.fixture.expectation.diagnostic["line"], repair["line"])
                self.assertNotIn("end_line", case.fixture.expectation.diagnostic)
                self.assertEqual(constructor_faults(bad, repair["anchor"], self.specs[name]["constructor"]), {case.rule})
                fixed_line = good.splitlines()[repair["line"]-1]
                self.assertEqual(constructor_faults(good, fixed_line, self.specs[name]["constructor"]), set())
                for line in good.splitlines():
                    if line.startswith("value="):
                        self.assertEqual(constructor_faults(good, line, self.specs[name]["constructor"]), set())

    def test_preserved_source_identities_definitions_duties_and_pending_partition(self):
        fields = ["id", "title", "source", "source_units", "category", "diagnostic_obligation",
                  "definition", "facets", "dependencies", "oracle_limitation"]
        protected = {k: self.catalogue[k] for k in ["subunits", "accounting"]}
        protected["requirements"] = [{k: r[k] for k in fields if k in r}
                                     for r in self.catalogue["requirements"]]
        digest = hashlib.sha256(json.dumps(protected, sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest, "db9a0d349d59596546460c5e14fc798987d530dc93db48751ee0ac337c52bb8c")
        pending = {r["id"]: r["pending"] for r in self.catalogue["requirements"]}
        self.assertEqual(hashlib.sha256(json.dumps(pending, sort_keys=True).encode()).hexdigest(),
                         "79ff284827e92839f2ec69b5fdfb732a55c2563748f3bb904ff72a7434af9335")
        coverage = {}
        for case in self.cases.values():
            coverage.setdefault(case.rule, set()).update(case.meta.facets)
        self.assertEqual(coverage, {r: set(fs) for r, fs in generated.ELIGIBLE.items()})
        self.assertEqual(sum(map(len, coverage.values())), 20)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 44)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 98)
        runtime_coverage = {}
        for family in (runtime_generated, batch317_generated):
            for rule, facets in family.FACETS_BY_RULE.items():
                runtime_coverage.setdefault(rule, set()).update(facets)
        self.assertEqual(sum(map(len, runtime_coverage.values())), 32)
        for r in self.catalogue["requirements"]:
            direct = (coverage.get(r["id"], set()) | generated.EXISTING.get(r["id"], set())
                      | runtime_coverage.get(r["id"], set()))
            self.assertEqual(set(r["pending"]), set(r["facets"]) - direct)
        self.assertEqual(self.registry.accounting["7.5.10"]["note4"]["disposition"], "structural")
        self.assertEqual(self.registry.accounting["7.5.10"]["note4.2"]["disposition"], "structural")
        self.assertEqual(self.registry.accounting["7.5.10"]["note4.embedded-note-reference"]["disposition"],
                         "structural")
        self.assertEqual(self.registry.accounting["7.5.10"]["note4.2.genuine-note4-person-value"]["disposition"],
                         "informative")
        self.assertIn("note4.embedded-note-reference", self.catalogue["subunits"]["note4"])

    def test_complete_pending_appendix_and_administrative_review_transitions(self):
        view = (ROOT / generated.VIEW).read_text()
        self.assertIn("Catalogue source review:", view)
        self.assertIn("## Complete finite pending plans", view)
        appendix = view.split("## Complete finite pending plans\n", 1)[1].split("## Reproduction and separate gates", 1)[0]
        self.assertEqual(appendix.count("* **`"), 44)
        for r in self.catalogue["requirements"]:
            for facet, plan in r["pending"].items():
                self.assertIn(f"* **`{facet}`** - {plan}", appendix)
        self.assertEqual(runtime_generated.synced_catalogue(self.catalogue), self.catalogue)
        self.assertEqual(batch317_generated.synced_catalogue(self.catalogue), self.catalogue)
        corrupted = copy.deepcopy(self.catalogue)
        by_rule = {row["id"]: row for row in corrupted["requirements"]}
        by_rule["R756"]["pending"].pop("required-parentheses")
        with self.assertRaisesRegex(ValueError, "pending partition mismatch: R756"):
            generated.synced_catalogue(corrupted, self.specs)
        with self.assertRaisesRegex(ValueError, "pending partition mismatch: R756"):
            runtime_generated.synced_catalogue(corrupted)
        with self.assertRaisesRegex(ValueError, "pending partition mismatch: R756"):
            batch317_generated.synced_catalogue(corrupted)
        reviewed = copy.deepcopy(self.catalogue)
        reviewed["review_state"] = "reviewed"
        reviewed["review_rationale"] = "In-memory administrative transition; not an approval."
        r = Registry(ROOT)
        r.catalogues[generated.SECTION] = reviewed
        reviewed["review_fingerprint"] = r.catalogue_fingerprint(generated.SECTION)
        self.assertEqual(runtime_generated.synced_catalogue(reviewed), reviewed)
        self.assertEqual(batch317_generated.synced_catalogue(reviewed), reviewed)
        reviewed["review_fingerprint"] = "0" * 64
        self.assertEqual(runtime_generated.synced_catalogue(reviewed), reviewed)

    def test_admission_facets_use_repairs_without_cloned_third_cases(self):
        for rule, facets in generated.ELIGIBLE.items():
            if rule in ("R756", "S7.5.10-006"):
                continue
            positives = {r["control"] for n, r in self.repairs.items() if self.cases[n].rule == rule}
            self.assertEqual(positives, {n for n, c in self.cases.items() if c.rule == rule and c.kind == "valid"})
        for variant in PAIRS["C7102"]:
            name = generated.identifier("C7102", variant, True)
            source = self.source(name)
            self.assertEqual(constructor_faults(source, "value=pair(left=11,right=11)", "pair"), set())
            self.assertEqual(constructor_faults(source, "value=pair(left=11,left=11)", "pair"),
                             {"C7102", "C7104"})
        name = generated.identifier("C7105", "keyword_order", True)
        self.assertEqual(constructor_faults(self.source(name), "value=pair(11,right=13)", "pair"), set())

    def test_abstract_ancestor_and_pdt_contexts_have_no_independent_defects(self):
        bad = self.source(generated.identifier("C7101", "abstract", True))
        self.assertNotIn("type(base)", bad.lower())
        self.assertNotIn("deferred", bad.lower())
        self.assertIn("class(base), intent(in) :: self", bad)
        parent = self.source(generated.identifier("C7103", "ancestor_overlap", True))
        self.assertIn("parent_value%x=11\nparent_value%y=13\n", parent)
        self.assertNotRegex(parent, r"parent_value\s*=\s*parent\(")
        self.assertEqual(type_model(parent)["child"]["order"], ["x", "y", "z"])
        pdt = self.source(generated.identifier("C7106", "parameter_keyword", True))
        model = type_model(pdt)["packet"]
        self.assertEqual(model["parameters"], ["k"])
        self.assertEqual(set(model["fields"]), {"payload"})
        self.assertIn("type(packet(k=2)) :: value", pdt)
        self.assertIn("packet(k=2)(payload=17,k=3)", pdt)
        self.assertNotRegex(pdt, r"integer\s*\(\s*k\s*\)")
        self.assertNotIn("packet()", pdt)

    def test_target_category_and_rank_repairs_keep_real_defaults_and_live_targets(self):
        for variant in PAIRS["C7109"]:
            name = generated.identifier("C7109", variant, True)
            source = self.source(name)
            fields = type_model(source)["holder"]["fields"]
            self.assertTrue(fields["p"]["default"] and fields["action"]["default"])
            self.assertEqual(fields["p"]["category"], "pointer")
            self.assertEqual(fields["action"]["category"], "procedure")
            self.assertIn("procedure(action_interface), pointer, nopass :: action=>null()", source)
            self.assertIn("subroutine action_interface()\nend subroutine action_interface", source)
            self.assertIn("subroutine worker()\nend subroutine worker", source)
            self.assertIn("integer, target :: datum", source)
            self.assertLess(source.index("datum=17"), source.index("value=holder("))
            self.assertNotIn("call worker", source)
        for variant in PAIRS["C7110"]:
            name = generated.identifier("C7110", variant, True)
            good = self.source(self.repairs[name]["control"])
            self.assertEqual(target_model(good)["vec"], 1)
            self.assertEqual(target_model(good)["scalar_target"], 0)
            self.assertIn("vec(1)=11\nvec(2)=13", good)
            self.assertEqual(type_model(good)["holder"]["fields"]["one"]["rank"], 0)
            self.assertEqual(type_model(good)["holder"]["fields"]["many"]["rank"], 1)
            for line in generated.POINTER_CONTEXTS.splitlines():
                if line.startswith("value="):
                    self.assertEqual(constructor_faults(good, line, "holder"), set())
            self.assertEqual(constructor_faults(good, "value=holder(one=null(mold=array_mold))", "holder"),
                             {"C7110"})
            self.assertEqual(constructor_faults(good, "value=holder(many=null(mold=scalar_mold))", "holder"),
                             {"C7110"})
            altered = good.replace("integer, pointer :: many(:)=>null()", "integer, pointer :: many(:)")
            self.assertEqual(constructor_faults(altered, "value=holder(one=scalar_target)", "holder"), {"C7104"})

    def test_every_cause_at_normal_status_zero_and_one(self):
        checks = 0
        for name in self.repairs:
            condition = self.cases[name].fixture.expectation.diagnostic
            self.assertFalse(condition.get("allow_nonfatal"))
            for message in condition["contains_any"]:
                for family in ("lfortran", "gfortran", "flang"):
                    for status in (0, 1):
                        with self.subTest(case=name, message=message, family=family, status=status):
                            result = self.judge(name, message, family, status)
                            self.assertEqual(result.outcome, "pass")
                            self.assertEqual(result.note, "diagnoses without rejection" if status == 0 else "rejects")
                            checks += 1
        self.assertGreaterEqual(checks, 400)

    def test_finite_wrong_subject_property_and_source_probes(self):
        probes = 0
        for name in self.repairs:
            case = self.cases[name]
            message = case.fixture.expectation.diagnostic["contains_any"][0]
            for family in ("lfortran", "gfortran", "flang"):
                for status in (0, 1):
                    for wrong in WRONG_CAUSES[case.rule]:
                        with self.subTest(case=name, family=family, wrong=wrong):
                            self.assertEqual(self.judge(name, wrong, family, status).outcome, "fail")
                            probes += 1
                    self.assertEqual(self.judge(name, message, family, status, filename="wrong.f90").outcome, "fail")
                    self.assertEqual(self.judge(name, message, family, status, line=1).outcome, "fail")
                    self.assertEqual(self.judge(name, message, family, status, echo=True).outcome, "fail")
        self.assertGreaterEqual(probes, 300)

    def test_every_cause_rejects_unsupported_wrappers_and_generic_recovery(self):
        wrappers = ["Unsupported: ", "This feature is unsupported by this compiler: ",
                    "Not implemented: ", "Not supported: ", "Unexpected end of file: ",
                    "Missing END MODULE: "]
        for name in self.repairs:
            for message in self.cases[name].fixture.expectation.diagnostic["contains_any"]:
                for family in ("lfortran", "gfortran", "flang"):
                    for code in (0, 1):
                        for wrapper in wrappers:
                            with self.subTest(case=name, family=family, wrapper=wrapper):
                                self.assertEqual(self.judge(name, wrapper+message, family, code).outcome, "fail")

    def test_native_predicates_keep_case_specific_role_and_rank_premises(self):
        for name, repair in self.repairs.items():
            spec = self.specs[name]
            more_wrong = ["Keyword argument is already specified", "Keyword argument not found",
                          "Argument was not specified"]
            if spec["variant"] == "positional_repeat":
                more_wrong.append("Keyword 'left' at (1) has already appeared in the current argument list")
            if spec["variant"] == "array_to_scalar":
                more_wrong.extend([
                    "Pointer has rank 1 but target has rank 0",
                    "Pointer has rank 0 but target has rank 10",
                    "Data target 'vec' has rank 1 but pointer component 'one' has rank 01.",
                ])
            if spec["variant"] == "scalar_to_array":
                more_wrong.extend([
                    "Pointer has rank 0 but target has rank 1",
                    "Pointer has rank 1 but target has rank 01",
                    "Data target 'scalar_target' has rank 0 but pointer component 'many' has rank 10.",
                ])
            for family in ("lfortran", "gfortran", "flang"):
                for code in (0, 1):
                    for message in more_wrong:
                        self.assertEqual(self.judge(name, message, family, code).outcome, "fail")

    def test_nonfatal_family_permissions_and_internal_guard_are_separate(self):
        for name in self.repairs:
            original = self.cases[name].fixture.expectation.diagnostic
            message = original["contains_any"][0]
            predicate = copy.deepcopy(original)
            predicate["allow_nonfatal"] = [dict(compiler="flang", severity="warning", equals_any=[message])]
            for code in (0, 1):
                self.assertEqual(self.judge(name, message, "flang", code, severity="warning").outcome, "fail")
                self.assertEqual(self.judge(name, message, "flang", code, severity="warning",
                                           predicate=predicate).outcome, "pass")
                self.assertEqual(self.judge(name, message, "gfortran", code, severity="warning",
                                           predicate=predicate).outcome, "fail")
                self.assertEqual(self.judge(name, message+" unrelated extension", "flang", code,
                                           severity="warning", predicate=predicate).outcome, "fail")
                suffix = f"{original['file']}:1:1: error: Internal: no symbol found\n"
                self.assertEqual(self.judge(name, message, "flang", code, severity="warning",
                                           predicate=predicate, suffix=suffix).outcome, "fail")

    def test_compiler_failure_cannot_be_masked_by_any_matching_cause(self):
        for name in self.repairs:
            message = self.cases[name].fixture.expectation.diagnostic["contains_any"][0]
            for family in ("lfortran", "gfortran", "flang"):
                self.assertEqual(self.judge(name, message, family, -11).outcome, "fail")
                self.assertEqual(self.judge(name, message, family, 139).outcome, "fail")
                self.assertEqual(self.judge(name, message, family, 0, timed_out=True).outcome, "fail")
                for suffix in ["Internal Compiler Error: failure\n", "ASR verify pass error\n",
                               "LLVM ERROR: verifier failure\n", "out of memory\n",
                               "unknown.f90:1:1: error: Internal: no symbol found\n"]:
                    self.assertEqual(self.judge(name, message, family, 1, suffix=suffix).outcome, "fail")

    def test_existing_c7107_primary_inputs_and_represented_facets_are_unchanged(self):
        expected = {
            "C7107_invalid__initialization_default_private": "fc6536533fd31d3f456da3e8edcdc7b0adb35c807f02fe87a55b86dc161c0090",
            "C7107_invalid__initialization_explicit_private": "3f1645269c05d3e0765d9e51cef8e9606cf9e1d67100c79746934d113a8d4641",
            "C7107_valid__initialization_default_private_repair": "ac5ca9dbf24f2cfac8e972ec6488c75300b9c5a2d7f97e79b5e942e048e86ee0",
            "C7107_valid__initialization_explicit_private_repair": "eb1a6938742ca80e0b9ecef89f706a8d0a343703f5aedaa3d2fe516689ef4023",
        }
        self.assertEqual(set(self.legacy), set(expected))
        for name, case in self.legacy.items():
            self.assertEqual(case.fingerprint(self.registry), expected[name])
            self.assertEqual(case.fixture.expectation.phase, "compile")
            self.assertEqual(case.meta.evidence, "effect" if case.kind == "invalid" else "positive-control")
            self.assertFalse(set(case.fixture.root / p for p in case.fixture.files) & set(self.outputs))


if __name__ == "__main__":
    unittest.main()
