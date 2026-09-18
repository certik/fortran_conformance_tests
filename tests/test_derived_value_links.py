"""Finite singleton links retain canonical sources, gates and execution identity."""
from collections import Counter
import contextlib
import copy
from dataclasses import asdict
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from evidence_links import qualifying_reference
from execution_aggregates import observations
from execution_commands import command_plan, execution_context
from suite_data import Registry, SuiteError, case_review_bindings, write_json


ROOT = Path(__file__).resolve().parents[1]
LINKS = "doc/evidence/canonical_case_links.json"
TARGET = "doc/catalogues/derived_types_7_5_8.json"
ASSIGNMENT = "doc/catalogues/assignment.json"
POINTER_ANCHORS = ("p1.pointer-component", "p1.pointer-association-value")
ORDINARY_ANCHORS = ("p1.nonpointer-nonallocatable", "p1.ordinary-component-value")
MATRIX = [
    ("S7.5.8-001", "data-pointer-association", 24, "p15.pointer", POINTER_ANCHORS),
    ("S7.5.8-001", "array-pointer-association", 24, "p15.pointer", POINTER_ANCHORS),
    ("S7.5.8-001", "procedure-pointer-association", 24, "p15.pointer", POINTER_ANCHORS),
    ("S7.5.8-001", "disassociated-pointer-value", 24, "p15.pointer", POINTER_ANCHORS),
    ("S7.5.8-002", "unallocated-status", 29, "p15.i1", ("p1.allocatable-status",)),
    ("S7.5.8-002", "allocated-status", 30, "p15.i2", ("p1.allocatable-status", "p1.allocated-condition")),
    ("S7.5.8-002", "allocated-dynamic-type", 30, "p15.i2",
     ("p1.allocated-condition", "p1.allocated-dynamic-type")),
    ("S7.5.8-002", "allocated-type-parameters", 30, "p15.i2",
     ("p1.allocated-condition", "p1.allocated-type-parameters")),
    ("S7.5.8-002", "allocated-bounds", 30, "p15.i2", ("p1.allocated-condition", "p1.allocated-bounds")),
    ("S7.5.8-002", "allocated-data-value", 32, "p15.i2", ("p1.allocated-condition", "p1.allocated-value")),
    ("S7.5.8-003", "ordinary-intrinsic-components", 26, "p15.ordinary-intrinsic", ORDINARY_ANCHORS),
    ("S7.5.8-003", "ordinary-nested-derived-component", 26, "p15.ordinary-intrinsic", ORDINARY_ANCHORS),
    ("S7.5.8-003", "ordinary-array-components", 26, "p15.ordinary-intrinsic", ORDINARY_ANCHORS),
]
INPUT_HASHES = {
    24: "af26da1b6d999be90b11d100022780376cfd7ef2f799202208b537fccedf1a56",
    26: "337b7200e9264ff0371539e03a103d63d64abb44e29b990bb537af447d7b334f",
    29: "975e9b1554bc1336a844f728458993e933244b2993e3c12341f4a39b6331461a",
    30: "72f65d432a5f94349cda0fd44bb551e94afbab46e8c62a163a4db332d636dee7",
    32: "52d921d950920f249a691e8f66f2a5b2d86fc58d6341fe1f8d698dfe3aa07fe3",
}
CASE_IDS = {f"S10_2_1_3_{number:03d}_valid" for number in INPUT_HASHES}
LINK_IDS = {requirement + "." + facet for requirement, facet, _, _, _ in MATRIX}


class DerivedValueLinksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(prefix="derived-value-links-tests-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.root = Path(cls.directory.name).resolve()
        for name in ("doc", "tests"):
            shutil.copytree(ROOT / name, cls.root / name, ignore=shutil.ignore_patterns("__pycache__"))
        cls.original = Registry(cls.root)
        cls.original_cases = runner.collect_cases(cls.root / "tests", cls.original)
        cls.original_members = cls.original.execution._members(cls.original_cases)
        cls.original_links = cls.original.evidence.snapshot(cls.original_cases)

    def setUp(self):
        self.saved = {}
        for name in (LINKS, TARGET, "tests/reviews.json"):
            self.protect(name)
        self.registry = Registry(self.root)
        self.cases = copy.deepcopy(self.original_cases)
        self.registry.validate_cases(self.cases)
        self.by_id = {case.name: case for case in self.cases}

    def tearDown(self):
        for path, raw in self.saved.items():
            path.write_bytes(raw)

    def protect(self, relative):
        path = self.root / relative
        self.saved.setdefault(path, path.read_bytes())
        return path

    def change_json(self, relative, change):
        path = self.protect(relative)
        data = json.loads(path.read_text())
        change(data)
        write_json(path, data)

    def sources(self):
        return {number: (self.root / f"tests/clause10/S10_2_1_3_{number:03d}_valid.f90").read_text()
                for number in INPUT_HASHES}

    def own_reports(self, registry=None, cases=None):
        return {row["id"]: row for row in (registry or self.registry).evidence.report(
            self.cases if cases is None else cases) if row["id"] in LINK_IDS}

    def make_current(self, identifier="S7.5.8-001.data-pointer-association"):
        registry = Registry(self.root)
        registry.record_catalogue_review("7.5.8", "Synthetic test-only source adjudication in a disposable full copy.")
        cases = copy.deepcopy(self.cases)
        registry.validate_cases(cases)
        registry.evidence.record_review(
            cases, identifier, "source-reviewed", "Synthetic connection gate control, never a repository approval.")
        self.assertEqual(self.own_reports(registry, cases)[identifier]["state"], "current")
        return registry, cases, identifier

    def test_exact_thirteen_singletons_keep_owners_paths_roles_phases_and_anchors(self):
        reports = self.own_reports()
        self.assertEqual(set(reports), LINK_IDS)
        self.assertEqual({(row["target"]["requirement"], row["target"]["facet"]) for row in reports.values()},
                         {(requirement, facet) for requirement, facet, _, _, _ in MATRIX})
        for requirement, facet, number, primary_unit, target_units in MATRIX:
            with self.subTest(facet=facet):
                link = self.registry.evidence.links[requirement + "." + facet]
                identifier = f"S10_2_1_3_{number:03d}_valid"
                owner = f"S10.2.1.3-{number:03d}"
                source = "10.2.1.3#" + primary_unit
                self.assertEqual(link["pattern"], "runtime-effect")
                self.assertEqual(link["target"]["source_units"], ["7.5.8#" + unit for unit in target_units])
                self.assertEqual(link["cases"], [
                    dict(id=identifier, role="runtime-effect", primary_rule=owner, source=source,
                         path=f"tests/clause10/{identifier}.f90", phase="run")])
                self.assertTrue({source, "10.2.1.3#p1", "10.2.1.3#p15", "10.2.1.3#p16"} <= set(link["basis"]))
                case = self.by_id[identifier]
                self.assertEqual((case.rule, case.kind, case.meta.evidence), (owner, "valid", "effect"))
                self.assertEqual(case.meta.oracle_basis, "standard")
                self.assertEqual(case.meta.standard, "")
                self.assertFalse(case.meta.profiles)
                self.assertFalse(case.meta.coarray)
                self.assertEqual(case.meta.images, 1)
                self.assertIsNone(case.fixture)
                self.assertNotIn("positive_control_facets", self.registry.requirements[requirement])
                self.assertEqual(reports[link["id"]]["observation_aggregation"], "not-computed")

    def test_scoped_accounting_and_p2_definition_do_not_add_executions(self):
        target = self.registry.catalogues["7.5.8"]
        self.assertEqual(len(target["requirements"]), 3)
        self.assertEqual(sum(len(row["facets"]) for row in target["requirements"]), 13)
        self.assertEqual(sum(len(row["pending"]) for row in target["requirements"]), 0)
        self.assertEqual(set(self.registry.sections["7.5.8"]["units"]), {"p1", "p2"})
        self.assertEqual(sum(map(len, target["subunits"].values())), 14)
        for row in target["accounting"]:
            if row["unit"] == "p2" or row["unit"].startswith("p2."):
                self.assertEqual(row["disposition"], "definition")
                self.assertNotIn("requirements", row)
        self.assertNotIn("S7.5.8-004", self.registry.requirements)
        self.assertFalse(any(case.rule.startswith("S7.5.8-") for case in self.cases))
        self.assertEqual({case.name for case in self.cases}, {case.name for case in self.original_cases})
        self.assertEqual(case_review_bindings(self.cases, self.registry),
                         case_review_bindings(self.original_cases, self.original))
        self.registry.render()

    def test_exact_input_bytes_and_selector_suffixes_exclude_finalization_variant(self):
        for number, text in self.sources().items():
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(), INPUT_HASHES[number])
        selected = runner.select_cases(self.cases, [identifier + ".f90" for identifier in sorted(CASE_IDS)])
        self.assertEqual({case.name for case in selected}, CASE_IDS)
        broad = runner.select_cases(self.cases, ["S10_2_1_3_029_valid"])
        self.assertIn("S10_2_1_3_029_valid__finalization", {case.name for case in broad})
        self.assertNotIn("S10_2_1_3_029_valid__finalization", {case.name for case in selected})
        self.assertEqual(Counter(row["cases"][0]["id"] for row in self.own_reports().values()), {
            "S10_2_1_3_024_valid": 4, "S10_2_1_3_026_valid": 3, "S10_2_1_3_029_valid": 1,
            "S10_2_1_3_030_valid": 4, "S10_2_1_3_032_valid": 1})

    def test_pointer_literals_identity_interfaces_and_defined_nullification(self):
        source = self.sources()[24]
        for fragment in (
            "integer, target :: scalar, values(6)", "scalar = 17", "values = [2, 3, 5, 7, 11, 13]",
            "source%scalar => scalar", "source%values => values(2:6:2)", "source%action => double_value",
            "procedure(transform), pointer, nopass :: action => null()",
            "integer function transform(n)", "integer function double_value(n)", "double_value = 2 * n",
            "if (.not. associated(copy%scalar, scalar)) error stop 'data-pointer'",
            "if (.not. associated(copy%values, values(2:6:2))) error stop 'array-pointer'",
            "if (.not. associated(copy%action, double_value)) error stop 'procedure-pointer'",
            "if (copy%action(5) /= 10) error stop 'procedure-call'",
            "copy%scalar = 41", "copy%values(2) = 43",
            "if (scalar /= 41 .or. values(4) /= 43) error stop 'shared-live-targets'",
        ):
            self.assertIn(fragment, source)
        self.assertEqual(source.count("integer, intent(in) :: n"), 2)
        self.assertEqual(source.count("copy = source"), 2)
        nullified = source.split("nullify(source%scalar, source%values, source%action)", 1)[1]
        self.assertLess(nullified.index("copy = source"), nullified.index("if (associated(copy%scalar))"))
        for component in ("scalar", "values", "action"):
            self.assertIn(f"if (associated(copy%{component})) error stop", nullified)
        self.assertNotIn("deallocate", source.lower())

    def test_unallocated_and_allocated_only_observers_have_independent_premises(self):
        plain, allocated = self.sources()[29], self.sources()[30]
        before, after = plain.split("copy = source", 1)
        self.assertNotIn("source%values", before)
        self.assertIn("allocate(copy%values(2))", before)
        self.assertIn("copy%values = [2, 5]", before)
        self.assertIn("source%tag = 17", before)
        for label in ("allocated-to-unallocated", "both-unallocated"):
            self.assertIn(f"if (allocated(copy%values)) error stop '{label}'", after)
        self.assertNotIn("final ::", plain)
        for component in ("object", "number", "values", "text"):
            for parent in ("copy", "source"):
                guard = f"if (.not. allocated({parent}%{component}))"
                self.assertLess(allocated.index(guard), allocated.index("select type (object => copy%object)"))
        for fragment in (
            "integer, parameter :: dp = kind(0.0d0)", "allocate(child :: source%object)",
            "source%number = 1.5_dp", "source%text = 'abc'",
            "type is (real(kind=dp))", "if (number /= 1.5_dp) error stop 'kind-value'",
            "error stop 'kind-parameter'", "error stop 'dynamic-type'",
            "if (object%n /= 17 .or. object%extra /= 31) error stop 'dynamic-type-value'",
            "if (len(copy%text) /= 3 .or. copy%text /= 'abc') error stop 'length-parameter'",
            "allocate(source%values(-2:0))", "if (size(copy%values) /= 3) error stop 'array-shape'",
            "if (lbound(copy%values, 1) /= -2 .or. ubound(copy%values, 1) /= 0) error stop 'nonunit-bounds'",
            "if (any(copy%values /= [2, 5, 9])) error stop 'array-value'",
        ):
            self.assertIn(fragment, allocated)
        empty = allocated.split("allocate(source%values(0))", 1)[1]
        self.assertLess(empty.index("allocated(copy%values)"), empty.index("size(copy%values)"))
        self.assertLess(empty.index("allocated(copy%text)"), empty.index("len(copy%text)"))
        self.assertIn("size(copy%values) /= 0 .or. len(copy%text) /= 0", empty)
        self.assertNotIn("lbound", empty)
        self.assertNotIn("ubound", empty)

    def test_allocated_data_value_keeps_declared_generic_context_and_all_literals(self):
        source = self.sources()[32]
        base = source.split("type :: base", 1)[1].split("end type", 1)[0]
        child = source.split("type, extends(base) :: child", 1)[1].split("end type", 1)[0]
        self.assertNotIn("contains", base)
        self.assertIn("generic :: assignment(=) => assign_child", child)
        self.assertIn("class(base), allocatable :: object", source)
        for fragment in (
            "object%n = 17", "object%extra = 31", "object%nested = [2, 5, 9]",
            "source%values = [11, 13]", "if (any(copy%values /= [11, 13]))",
            "if (object%n /= 17 .or. object%extra /= 31)",
            "if (.not. allocated(object%nested))", "if (size(object%nested) /= 3)",
            "if (any(object%nested /= [2, 5, 9]))", "object%nested(1) = -19",
            "if (wrong_calls /= 0) error stop 'dynamic-only-binding-control'",
            "if (object%nested(1) /= 2) error stop 'nested-independent-storage'",
        ):
            self.assertIn(fragment, source)
        self.assertLess(source.index("allocated(copy%object)"), source.index("select type (object => copy%object)"))
        self.assertLess(source.index("allocated(copy%values)"), source.index("size(copy%values)"))
        destination = source.split("select type (object => copy%object)", 1)[1].split("end select", 1)[0]
        self.assertLess(destination.index("allocated(object%nested)"), destination.index("size(object%nested)"))
        self.assertLess(destination.index("size(object%nested)"), destination.index("any(object%nested"))

    def test_ordinary_component_checks_are_initialized_literals_without_defined_assignment(self):
        source = self.sources()[26]
        for name in ("inner", "packet"):
            body = source.split("type :: " + name, 1)[1].split("end type", 1)[0]
            for forbidden in ("contains", "pointer", "allocatable", "generic"):
                self.assertNotIn(forbidden, body)
        for fragment in (
            "source%tag = 17", "source%text = 'abc'", "source%flag = .true.",
            "source%scalar%n = 23", "source%scalar%x = 1.5",
            "source%values(1)%n = 31", "source%values(1)%x = 2.5",
            "source%values(2)%n = 43", "source%values(2)%x = -3.5",
        ):
            self.assertLess(source.index(fragment), source.index("copy = source"))
        for fragment in (
            "copy%tag /= 17 .or. copy%text /= 'abc' .or. .not. copy%flag",
            "copy%scalar%n /= 23 .or. copy%scalar%x /= 1.5",
            "copy%values(1)%n /= 31 .or. copy%values(1)%x /= 2.5",
            "copy%values(2)%n /= 43 .or. copy%values(2)%x /= -3.5",
            "copy%values(1)%n = -1",
            "if (source%values(1)%n /= 31) error stop 'independent-components'",
        ):
            self.assertIn(fragment, source)

    def test_malformed_singleton_owner_anchor_role_and_phase_use_shared_validation(self):
        original = copy.deepcopy(self.registry.evidence.data)
        identifier = "S7.5.8-001.data-pointer-association"
        mutations = [
            lambda link: link["cases"].append(copy.deepcopy(link["cases"][0])),
            lambda link: link["cases"][0].update(role="positive-control"),
            lambda link: link["cases"][0].update(phase="compile"),
            lambda link: link["cases"][0].update(primary_rule="S10.2.1.3-026"),
            lambda link: link["cases"][0].update(source="10.2.1.3#p1"),
            lambda link: link["cases"][0].update(path="tests/clause10/S10_2_1_3_026_valid.f90"),
            lambda link: link["target"].update(source_units=["7.5.8#p1"]),
            lambda link: link["basis"].remove("10.2.1.3#p15.pointer"),
            lambda link: link.update(pattern="positive-control"),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                data = copy.deepcopy(original)
                mutate(next(row for row in data["links"] if row["id"] == identifier))
                write_json(self.root / LINKS, data)
                with self.assertRaises(SuiteError):
                    runner.collect_cases(self.root / "tests", Registry(self.root))

    def test_removing_a_declared_link_exposes_pending_instead_of_hiding_the_facet(self):
        registry = copy.deepcopy(self.registry)
        identifier = "S7.5.8-002.allocated-bounds"
        link = registry.evidence.links.pop(identifier)
        with self.assertRaisesRegex(SuiteError, "uncovered facets"):
            registry.validate_cases(self.cases)
        registry.requirements[link["target"]["requirement"]]["pending"][link["target"]["facet"]] = (
            "Synthetic missing-link gate, not a repository edit.")
        registry.validate_cases(self.cases)
        self.assertNotIn(identifier, self.own_reports(registry))
        self.assertEqual({case.name for case in self.cases}, {case.name for case in self.original_cases})

    def test_missing_canonical_case_or_source_catalogue_cannot_erase_the_gate(self):
        without_member = [case for case in self.cases if case.name != "S10_2_1_3_024_valid"]
        with self.assertRaisesRegex(SuiteError, "unknown canonical case ID"):
            self.registry.evidence.report(without_member)
        self.change_json("doc/catalogues/index.json", lambda data: data["catalogues"].remove(ASSIGNMENT))
        with self.assertRaises(SuiteError):
            Registry(self.root)

    def test_current_canonical_metadata_still_uses_shared_role_and_policy_validation(self):
        for mutation in ("positive-control", "context-only", "unknown-facet", "policy"):
            with self.subTest(mutation=mutation):
                cases = copy.deepcopy(self.cases)
                case = next(case for case in cases if case.name == "S10_2_1_3_024_valid")
                if mutation in ("positive-control", "context-only"):
                    case.meta.evidence = mutation
                elif mutation == "unknown-facet":
                    case.meta.facets = ["invented-association"]
                else:
                    case.meta.oracle_basis = "lfortran-policy"
                with self.assertRaises(SuiteError):
                    self.registry.validate_cases(cases)

    def test_source_review_gate_is_not_bypassed_by_current_case_reviews(self):
        registry, cases, identifier = self.make_current()
        for section in ("7.5.8", "10.2.1.3"):
            for state in ("draft", "stale"):
                with self.subTest(section=section, state=state):
                    changed = copy.deepcopy(registry)
                    if state == "draft":
                        changed.catalogues[section]["review_state"] = "draft"
                    else:
                        changed.catalogues[section]["review_fingerprint"] = "0" * 64
                    report = self.own_reports(changed, cases)[identifier]
                    self.assertIn(f"{section}: catalogue source review is {state}", report["blockers"])
                    self.assertNotEqual(report["state"], "current")
                    before = (self.root / LINKS).read_bytes()
                    with self.assertRaisesRegex(SuiteError, "catalogue source review"):
                        changed.evidence.record_review(cases, identifier, "source-reviewed", "Cannot bypass.")
                    self.assertEqual((self.root / LINKS).read_bytes(), before)

    def test_missing_and_unapproved_case_adjudications_block_the_connection(self):
        registry, cases, identifier = self.make_current()
        case = next(case for case in cases if case.name == "S10_2_1_3_024_valid")
        for state in (None, "unreviewed", "disputed", "needs-oracle", "stale"):
            with self.subTest(state=state):
                changed = copy.deepcopy(registry)
                if state is None:
                    changed.reviews.pop(case.review_key)
                elif state == "stale":
                    changed.reviews[case.review_key]["fingerprint"] = "0" * 64
                else:
                    changed.reviews[case.review_key]["state"] = state
                report = self.own_reports(changed, cases)[identifier]
                self.assertNotEqual(report["state"], "current")
                self.assertTrue(any("fixture review is" in text for text in report["blockers"]))
                before = (self.root / LINKS).read_bytes()
                with self.assertRaisesRegex(SuiteError, "fixture review is"):
                    changed.evidence.record_review(cases, identifier, "source-reviewed", "Cannot bypass.")
                self.assertEqual((self.root / LINKS).read_bytes(), before)

    def test_missing_unreviewed_and_stale_link_reviews_are_not_current(self):
        registry, cases, identifier = self.make_current()
        for state in (None, "unreviewed", "disputed", "needs-oracle", "stale"):
            with self.subTest(state=state):
                changed = copy.deepcopy(registry)
                link = changed.evidence.links[identifier]
                if state is None:
                    link.pop("review")
                elif state == "stale":
                    link["claim"] += " Changed connection meaning."
                else:
                    link["review"]["state"] = state
                self.assertNotEqual(self.own_reports(changed, cases)[identifier]["state"], "current")

    def test_mutated_canonical_input_and_generic_context_stale_exact_case_and_link(self):
        variants = [
            ("S7.5.8-001.data-pointer-association", 24, "copy%scalar = 41", "copy%scalar = 42"),
            ("S7.5.8-002.allocated-data-value", 32,
             "class(base), allocatable :: object", "class(child), allocatable :: object"),
        ]
        for identifier, number, old, new in variants:
            with self.subTest(case=number):
                registry, cases, identifier = self.make_current(identifier)
                path = self.protect(f"tests/clause10/S10_2_1_3_{number:03d}_valid.f90")
                raw = path.read_text()
                self.assertEqual(raw.count(old), 1)
                prior = self.own_reports(registry, cases)[identifier]
                path.write_text(raw.replace(old, new))
                changed = Registry(self.root)
                changed_cases = runner.collect_cases(self.root / "tests", changed)
                report = self.own_reports(changed, changed_cases)[identifier]
                self.assertEqual(report["cases"][0]["review"]["state"], "stale")
                self.assertEqual(report["state"], "stale")
                self.assertNotEqual(report["review"]["fingerprint"], prior["review"]["fingerprint"])
                self.assertEqual(len(changed_cases), len(self.cases))
                if number == 32:
                    self.assertIn("if (wrong_calls /= 0)", path.read_text())
                path.write_text(raw)

    def test_mutated_primary_requirement_original_unit_and_execution_group_stale_or_reject(self):
        registry, cases, identifier = self.make_current()
        for kind in ("requirement", "original-unit", "group"):
            with self.subTest(kind=kind):
                changed = copy.deepcopy(registry)
                if kind == "requirement":
                    changed.requirements["S10.2.1.3-024"]["oracle"] += " Changed premise."
                elif kind == "original-unit":
                    changed.sections["10.2.1.3"]["units"]["p15"]["sha256"] = "0" * 64
                else:
                    extra = copy.deepcopy(next(case for case in cases if case.name == "S10_2_1_3_024_valid"))
                    extra.name += ":new-group-member"
                    with self.assertRaisesRegex(SuiteError, "current execution set"):
                        changed.evidence.report(cases + [extra])
                    continue
                report = self.own_reports(changed, cases)[identifier]
                self.assertEqual(report["state"], "stale")
                self.assertEqual(report["source_reviews"]["10.2.1.3"]["state"], "stale")

    def test_own_lifecycle_preserves_complete_foreign_population_and_actual_states(self):
        before = self.registry
        before_members = before.execution._members(self.cases)
        before_reviews = copy.deepcopy(before.reviews)
        before_catalogues = copy.deepcopy(before.catalogues)
        before_links = copy.deepcopy(before.evidence.links)
        before_snapshot = before.evidence.snapshot(self.cases)
        registry, cases, _ = self.make_current()
        self.assertEqual(registry.execution._members(cases), before_members)
        self.assertEqual(registry.reviews, before_reviews)
        for section, catalogue in before_catalogues.items():
            if section != "7.5.8":
                self.assertEqual(registry.catalogues[section], catalogue)
        after_snapshot = registry.evidence.snapshot(cases)
        for identifier, link in before_links.items():
            if identifier not in LINK_IDS:
                self.assertEqual(registry.evidence.links[identifier], link)
                self.assertEqual(after_snapshot[identifier], before_snapshot[identifier])
        self.assertEqual(registry.source_uses.snapshot(), before.source_uses.snapshot())
        self.assertEqual(registry.execution.data, before.execution.data)
        inventory = registry.execution.report(cases, include_members=False)
        for item in inventory:
            self.assertEqual(set(item["member_ids"]), {case.name for case in cases})
            self.assertEqual(item["member_count"], len(cases))
            self.assertEqual(item["facet_completion"], "pending")
            self.assertEqual(item["universal_conformance"], "not-established")

    def synthetic_check(self, member, compiler, fail_phase=None):
        identity = dict(compiler.configuration(), version=compiler.version, c_binding_header={})
        context = execution_context(self.root / "synthetic-staging" / compiler.family / member["id"])
        plan = command_plan(member, identity, self.root, context)
        trace = [dict(step, returncode=0, timed_out=False, stdout="", stderr="",
                      stdout_hex="", stderr_hex="") for step in plan]
        if fail_phase == "compile-link":
            trace = trace[:1]
        if fail_phase:
            trace[-1].update(returncode=1, stderr="synthetic bounded failure",
                             stderr_hex=b"synthetic bounded failure".hex())
        return runner.Check(
            "fail" if fail_phase else "pass", phase=fail_phase or "run",
            trace=trace, input_hashes=member["input_hashes"], execution_context=context)

    def mock_cli(self, selected, fail=None):
        members = {row["id"]: row for row in self.registry.execution._members(
            [case for case in self.cases if case.name in CASE_IDS])}
        compilers = {
            name: runner.Compiler(name, name, mode, "synthetic, not native")
            for name, mode in (("lfortran", "f23"), ("gfortran", "f2023"), ("flang", "f2018"))}
        calls = []

        def execute(case, compiler, *args):
            calls.append((case.name, compiler.family))
            failure = (fail or {}).get((case.name, compiler.family))
            return self.synthetic_check(members[case.name], compiler, failure)

        report_path = self.root / "synthetic-report.json"
        arguments = ["run_tests.py", "--allow-unreviewed", "--reference", "gfortran",
                     "--reference", "flang", "--report", str(report_path)]
        for name in selected:
            arguments.extend(["--test", name + ".f90"])
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(runner, "HERE", str(self.root / "tests")), \
                patch.object(runner, "Registry", return_value=self.registry), \
                patch.object(runner, "compiler", side_effect=lambda name, *args: compilers[name]), \
                patch.object(runner, "execute_case", side_effect=execute), \
                patch.object(runner, "confirm_snapshot", return_value=[]), \
                patch.object(sys, "argv", arguments), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = runner.main()
        self.assertIn(code, (0, 1), stderr.getvalue() + stdout.getvalue())
        report = json.loads(report_path.read_text())
        self.assertEqual(report["run_errors"], [])
        return report, calls

    def test_full_current_population_deduplicates_five_cases_across_thirteen_occurrences(self):
        administrative = {path: (self.root / path).read_bytes() for path in (
            LINKS, TARGET, "tests/reviews.json", "tests/expected_failures.txt",
            "doc/evidence/whole_suite_execution.json", "doc/evidence/source_uses.json")}
        report, calls = self.mock_cli(sorted(CASE_IDS))
        self.assertEqual(len(calls), len(CASE_IDS) * 3)
        self.assertEqual(set(calls), {(identifier, family) for identifier in CASE_IDS
                                      for family in ("lfortran", "gfortran", "flang")})
        self.assertEqual({row["name"] for row in report["results"]}, CASE_IDS)
        own = [row for row in report["evidence_links"] if row["id"] in LINK_IDS]
        self.assertEqual(len(own), 13)
        for row in own:
            self.assertEqual(row["observation_aggregation"], "not-computed")
            member = row["cases"][0]
            self.assertEqual(member["observation_state"], "present")
            self.assertEqual(member["target_observation"]["standard"], "f23")
            self.assertEqual([value["standard"] for value in member["reference_observations"]], ["f2023", "f2018"])
        for aggregate in report["execution_aggregates"]:
            self.assertEqual(set(aggregate["member_ids"]), {case.name for case in self.cases})
            for projection in aggregate["observations"]:
                self.assertEqual(projection["population"], len(self.cases))
                selected = [row for row in projection["members"] if row["outcome"] != "not-selected"]
                self.assertEqual({row["id"] for row in selected}, CASE_IDS)
                self.assertFalse(projection["observation_set_complete"])
        for path, raw in administrative.items():
            self.assertEqual((self.root / path).read_bytes(), raw)

    def test_unsampled_members_and_compiler_failures_are_not_or_combined(self):
        identifier = "S10_2_1_3_024_valid"
        report, calls = self.mock_cli([identifier], {(identifier, "gfortran"): "compile-link",
                                                    (identifier, "lfortran"): "run"})
        self.assertEqual(len(calls), 3)
        for link in report["evidence_links"]:
            if link["id"] not in LINK_IDS:
                continue
            member = link["cases"][0]
            if member["id"] == identifier:
                self.assertEqual(member["target_observation"]["outcome"], "fail")
                by_family = {row["family"]: row for row in member["reference_observations"]}
                self.assertEqual((by_family["gfortran"]["outcome"], by_family["gfortran"]["phase"]),
                                 ("fail", "compile-link"))
                self.assertEqual((by_family["flang"]["outcome"], by_family["flang"]["standard"]), ("pass", "f2018"))
            else:
                self.assertEqual(member["observation_state"], "not-selected")
                self.assertIsNone(member["target_observation"])
                self.assertEqual(member["reference_observations"], [])
        case = self.by_id[identifier]
        self.assertTrue(qualifying_reference(case, dict(outcome="pass", phase="run", standard="f2018")))
        requires_f2023 = copy.deepcopy(case)
        requires_f2023.meta.standard = "f2023"
        self.assertFalse(qualifying_reference(requires_f2023, dict(outcome="pass", phase="run", standard="f2018")))
        self.assertFalse(qualifying_reference(case, dict(outcome="pass", phase="compile-link", standard="f2023")))

    def test_observation_input_root_profile_and_configuration_bindings_cannot_be_transplanted(self):
        identifier = "S10_2_1_3_024_valid"
        report, _ = self.mock_cli([identifier])
        aggregates = self.registry.execution.report(self.cases)
        for mutation in ("input", "fingerprint", "root", "mode", "profile", "missing-run", "unexplained-skip"):
            with self.subTest(mutation=mutation):
                rows = copy.deepcopy(report["results"])
                identities = copy.deepcopy(report["compilers"])
                source_root = self.root
                check = rows[0]["check"]
                if mutation == "input":
                    check["input_hashes"] = {"wrong.f90": "0" * 64}
                elif mutation == "fingerprint":
                    rows[0]["review"]["fingerprint"] = "0" * 64
                elif mutation == "root":
                    source_root = self.root / "wrong-root"
                elif mutation == "mode":
                    identities[0]["standard"] = "f18"
                elif mutation == "profile":
                    check["profile_checks"] = {"ieee-binary": {"outcome": "pass"}}
                elif mutation == "missing-run":
                    check["trace"] = check["trace"][:1]
                else:
                    check["outcome"] = "skip"
                with self.assertRaises(SuiteError):
                    observations(aggregates, rows, identities, False, source_root=source_root)


if __name__ == "__main__":
    unittest.main()
