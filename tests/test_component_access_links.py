from collections import Counter
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner


class ComponentAccessLinksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = runner.Registry()
        cls.cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.by_id = {case.name: case for case in cls.cases}
        cls.links = {
            name: link for name, link in cls.registry.evidence.links.items()
            if name.startswith("S7.5.4.8-")
        }

    def test_exact_finite_targets_and_canonical_ownership(self):
        targets = {
            "S7.5.4.8-001.explicit-private-override":
                ("S7.5.4.8-001", "private-overrides-public-default", "explicit"),
            "S7.5.4.8-001.private-default-constructor":
                ("S7.5.4.8-001", "private-default-constructor-link", "default"),
            "S7.5.4.8-002.foreign-private-constructor":
                ("S7.5.4.8-002", "foreign-constructor-exclusion-link", "default"),
        }
        self.assertEqual(set(self.links), set(targets))
        for name, (rule, facet, variant) in targets.items():
            link = self.links[name]
            self.assertEqual(link["target"]["requirement"], rule)
            self.assertEqual(link["target"]["facet"], facet)
            self.assertNotIn(facet, self.registry.requirements[rule]["pending"])
            expected_duty = "required" if rule == "S7.5.4.8-002" else "not-required"
            self.assertEqual(self.registry.requirements[rule]["diagnostic_obligation"], expected_duty)
            self.assertEqual({member["role"] for member in link["cases"]},
                             {"diagnostic", "positive-control"})
            self.assertEqual({member["id"] for member in link["cases"]}, {
                f"C7107_invalid__initialization_{variant}_private",
                f"C7107_valid__initialization_{variant}_private_repair",
            })
            for member in link["cases"]:
                self.assertEqual(member["primary_rule"], "C7107")
                self.assertEqual(member["source"], "7.5.10#C7107")
                self.assertEqual(member["phase"], "compile")

    def test_provider_privacy_is_the_only_repair_and_client_is_unchanged(self):
        for variant in ("explicit", "default"):
            bad = self.by_id[f"C7107_invalid__initialization_{variant}_private"].fixture
            good = self.by_id[f"C7107_valid__initialization_{variant}_private_repair"].fixture
            wrong, repair = ((", private", ", public") if variant == "explicit" else ("private\n", ""))
            provider = (bad.root / "provider.f90").read_text()
            self.assertEqual(provider.count(wrong), 1)
            self.assertEqual(provider.replace(wrong, repair, 1),
                             (good.root / "provider.f90").read_text())
            self.assertEqual((bad.root / "main.f90").read_bytes(),
                             (good.root / "main.f90").read_bytes())
            self.assertEqual(bad.expectation.step, "main")
            self.assertEqual(bad.expectation.diagnostic["file"], "main.f90")

    def test_reused_members_do_not_add_executions_or_passing_aggregates(self):
        memberships = Counter(member["id"] for link in self.links.values() for member in link["cases"])
        self.assertEqual(len(memberships), 4)
        self.assertEqual(sorted(memberships.values()), [1, 1, 2, 2])
        actual = Counter(case.name for case in self.cases)
        for name in memberships:
            self.assertEqual(actual[name], 1)
        for report in self.registry.evidence.report(self.cases):
            if report["id"] in self.links:
                self.assertEqual(report["observation_aggregation"], "not-computed")
        owner_cases = [case for case in self.cases if case.rule == "S7.5.4.8-002"]
        self.assertEqual(len(owner_cases), 3)
        self.assertTrue(all(case.meta.evidence == "positive-control" for case in owner_cases))

    def test_private_component_name_reporting_has_the_clause19_basis(self):
        requirement = self.registry.requirements["S7.5.4.8-002"]
        self.assertEqual(requirement["diagnostic_obligation"], "required")
        self.assertIn("19.3.4 p5", requirement["dependencies"])
        self.assertIn("4.2 p2(6)", requirement["dependencies"])
        self.assertEqual(self.registry.requirements["S7.5.4.8-001"]["diagnostic_obligation"],
                         "not-required")


if __name__ == "__main__":
    unittest.main()
