"""DO CONCURRENT additional-semantics fixture packet checks."""

import json
from dataclasses import replace
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_do_concurrent_semantics_fixtures as generated


class DoConcurrentSemanticsFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}
        cls.members = {row["id"]: row for row in cls.registry.execution._members(list(cls.cases.values()))}

    def test_exact_nine_owned_runtime_cases_and_twenty_two_facets(self):
        self.assertEqual(set(self.cases), {spec["id"] for spec in self.specs.values()})
        self.assertEqual(set(self.specs), set(self.cases))
        self.assertEqual(len(self.files), 18)
        self.assertEqual(len(self.cases), 9)
        self.assertEqual(sum(len(v) for v in generated.FACETS_BY_RULE.values()), 22)
        self.assertEqual({facet for case in self.cases.values() for facet in case.meta.facets},
                         {facet for facets in generated.FACETS_BY_RULE.values() for facet in facets})
        self.assertEqual({case.rule for case in self.cases.values()}, set(generated.FACETS_BY_RULE))
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual((case.kind, case.meta.evidence, case.meta.standard),
                             ("valid", spec["evidence"], "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles or case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(len(case.fixture.build), 1)
            step = case.fixture.build[0]
            self.assertEqual((step.id, step.source, step.language, step.form, step.output),
                             ("source", "source.f90", "fortran", "free", "source.o"))
            self.assertEqual(case.fixture.link, dict(driver="fortran", objects=["source.o"], output="program"))
            expect = case.fixture.expectation
            self.assertEqual((expect.phase, expect.outcome, expect.exit_code), ("run", "success", 0))
            self.assertEqual(expect.stdout, [spec["stdout"]])
            self.assertEqual(expect.stderr, [""])
            expected_cohort = "positive-control" if spec["evidence"] == "positive-control" else "runtime-effect"
            self.assertEqual(self.members[case.name]["cohort"], expected_cohort)

    def test_sources_are_ascii_self_checking_and_do_not_duplicate_form_packet(self):
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), len(spec["facets"]))
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertIn("do concurrent", source.lower())
            self.assertIn("checks = checks + 1", source)
            self.assertIn("write(*,'(a)') '" + spec["stdout"].strip() + "'", source)
            self.assertNotRegex(source.lower(), r"\b(real|complex|sync\s+all|num_images|this_image|advance\s*=)\b")
            self.assertNotRegex(source.lower(), r"\bprint\s*\*")
            for facet in spec["facets"]:
                self.assertIn("! covers: " + facet + "\n", source)

    def test_locality_sources_use_defined_values_and_nondefault_sentinels(self):
        local = self.specs[generated.identifier("local_entities")]["source"]
        self.assertIn("local_scalar = 17", local)
        self.assertIn("local_array = -444", local)
        self.assertIn("local(local_scalar, local_array)", local)
        self.assertIn("local_scalar = 100 + i", local)
        self.assertLess(local.index("local_scalar = 100 + i"), local.index("result(i) = local_array(i)"))
        self.assertIn("lbound(local_array, 1)", local)
        self.assertIn("ubound(local_array, 1)", local)
        self.assertIn("any(local_array /= -444)", local)
        local_init = self.specs[generated.identifier("local_init_defined")]["source"]
        self.assertIn("local_value = -222", local_init)
        self.assertIn("init_value = 7", local_init)
        self.assertIn("local(local_value) local_init(init_value)", local_init)
        self.assertLess(local_init.index("local_value = 100"), local_init.index("observed(i) = local_value + init_value"))
        self.assertIn("init_value /= 7", local_init)
        self.assertNotRegex(local + local_init, r"(?m)^\s*(?:local_value|local_scalar)\s*/=")

    def test_reduce_sources_are_order_independent_and_hand_discriminated(self):
        identities = self.specs[generated.identifier("reduce_identities")]["source"]
        for needle in (
            "reduce(+:sum_value)", "sum_value /= 60",
            "reduce(*:product_value)", "product_value /= 48",
            "reduce(ior:or_value)", "or_value /= 23",
            "reduce(iand:and_value)", "and_value /= 241",
            "reduce(ieor:xor_value)", "xor_value /= 33",
            "reduce(max:max_value)", "max_value /= 12",
            "reduce(min:min_value)", "min_value /= 16",
        ):
            self.assertIn(needle, identities)
        logical_identities = self.specs[generated.identifier("reduce_logical_identities")]["source"]
        for needle in (
            "reduce(.and.:and_identity)", ".not. and_identity",
            "reduce(.or.:or_identity)", "or_identity",
            "reduce(.eqv.:eqv_identity)", ".not. eqv_identity",
            "reduce(.neqv.:neqv_identity)", ".not. neqv_identity",
        ):
            self.assertIn(needle, logical_identities)
        logical_final = self.specs[generated.identifier("reduce_logical_final_update")]["source"]
        for needle in (
            "reduce(.and.:and_final)", "and_final = and_final .and. (i /= 2)", "if (and_final) then",
            "reduce(.or.:or_final)", "or_final = or_final .or. (i == 2)", "if (.not. or_final) then",
            "reduce(.eqv.:eqv_final)", "eqv_final = eqv_final .eqv. (i /= 2)", "if (eqv_final) then",
            "reduce(.neqv.:neqv_final)", "neqv_final = neqv_final .neqv. (i == 1)", "if (neqv_final) then",
        ):
            self.assertIn(needle, logical_final)
        for spec in self.specs.values():
            if spec["rule"] in {generated.RULE_REDUCE_INITIAL, generated.RULE_REDUCE_FORMS,
                                generated.RULE_REDUCE_FINAL, generated.RULE_REDUCE_ORDER}:
                source = spec["source"].lower()
                self.assertNotRegex(source, r"\b(real|complex)\b")
                self.assertNotRegex(source, r"\b(random_number|system_clock|cpu_time)\b")
                self.assertNotRegex(source, r"\bwrite\s*\([^)]*\)\s*(?:[^'\\n]|$)")
        self.assertTrue(generated.logical_reduce_operations_are_order_independent())

    def test_feature_mutation_matrix_binds_complete_parent_sources(self):
        total = 0
        for spec in self.specs.values():
            hashes = set()
            for plan in spec["mutations"]:
                mutant = generated.mutate_source(spec, plan)
                self.assertNotEqual(mutant, spec["source"])
                self.assertEqual(generated.sha(mutant.encode("ascii")), plan["mutant_sha256"])
                self.assertNotIn(spec["stdout"].strip() + " BAD", mutant)
                self.assertIn(spec["stdout"].strip(), mutant)
                self.assertTrue(any(token in plan["id"] for token in
                                    ("remove", "substitute", "local", "shared", "plus", "times",
                                     "ior", "iand", "ieor", "max", "min", "and", "or", "eqv", "neqv")))
                for item in plan["replacements"]:
                    self.assertEqual(spec["source"].count(item["expected"]), 1)
                    self.assertNotEqual(item["expected"], item["replacement"])
                    self.assertIn(item["replacement"], mutant)
                self.assertNotIn(plan["mutant_sha256"], hashes)
                hashes.add(plan["mutant_sha256"])
                total += 1
        self.assertEqual(total, 32)

    def test_identity_mutant_is_reported_as_survivor_by_matrix_logic(self):
        spec = self.specs[generated.identifier("local_entities")]
        plan = json.loads(json.dumps(spec["mutations"][0]))
        plan["replacements"][0]["replacement"] = plan["replacements"][0]["expected"]
        same = generated.mutate_source(spec, plan, allow_identical=True)
        self.assertEqual(same, spec["source"])
        with self.assertRaises(ValueError):
            generated.mutate_source(spec, plan)

    def test_catalogue_sync_removes_only_selected_pending_facets_and_regenerates_view(self):
        catalogue = self.registry.catalogues[generated.SECTION]
        by_rule = {row["id"]: row for row in catalogue["requirements"]}
        for rule, facets in generated.FACETS_BY_RULE.items():
            for facet in facets:
                self.assertNotIn(facet, by_rule[rule].get("pending", {}))
            self.assertEqual(set(by_rule[rule].get("pending", {})), generated.EXPECTED_REMAINING[rule])
            self.assertIn(generated.ORACLE_PREFIXES[rule], by_rule[rule]["oracle"])
            self.assertIn(generated.LIMIT_PREFIXES[rule], by_rule[rule]["oracle_limitation"])
        self.assertNotIn("reduce-logical-initial-identities", by_rule[generated.RULE_REDUCE_INITIAL]["pending"])
        self.assertNotIn("reduce-final-logical-result", by_rule[generated.RULE_REDUCE_FINAL]["pending"])
        synced = generated.synced_catalogue(catalogue)
        self.assertEqual(synced, catalogue)
        view = generated.render_view(synced)
        self.assertIn(generated.SUMMARY_BEGIN, view)
        self.assertIn("nine complete run/effect/f2023 programs", view.lower())
        self.assertIn("LOGICAL .AND., .OR., .EQV. and .NEQV.", view)

    def test_generation_is_deterministic_and_check_mode_is_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)

    def test_case_requirement_validation_rejects_bad_facets(self):
        for case in self.cases.values():
            requirement = self.registry.requirements[case.rule]
            validate_case_requirement(case, requirement, numbered=False)
            bad = replace(case, meta=replace(case.meta, facets=["foreign-facet"]))
            with self.assertRaises(SuiteError):
                validate_case_requirement(bad, requirement, numbered=False)


if __name__ == "__main__":
    unittest.main()
