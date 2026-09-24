"""Runtime fixtures for Fortran 2023 intrinsic procedures 16.9.92-16.9.94."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_intrinsics_16_9_k_fixtures as generated


class Intrinsics169KFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_exact_owned_manifest_set_and_metadata(self):
        expected = {generated.identifier(spec["variant"], spec["rule"]) for spec in self.specs.values()}
        self.assertEqual(set(self.cases), expected)
        self.assertEqual(set(self.specs), expected)
        self.assertEqual(len(self.files), 15)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 20)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for case in self.cases.values():
            spec = self.specs[case.name]
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual(case.meta.evidence, spec["evidence"])
            self.assertEqual((case.meta.standard, case.meta.oracle_basis, case.meta.images), ("f2023", "standard", 1))
            self.assertFalse(case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.profiles, spec["profiles"])
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(case.fixture.arguments, spec["arguments"])
            self.assertNotIn("env", spec["manifest"].get("run", {}))
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            validate_case_requirement(case, self.registry.requirements[case.rule])

    def test_sources_are_bounded_and_observe_only_profiled_branches(self):
        anchors = {
            "get_command_effects": [
                "call get_command(command_full, length_full, status_full)",
                "len_trim(command_full) <= length_full",
                "blank_after(command_full, length_full)",
            ],
            "get_command_status": [
                "call get_command(command_short, length_short, status_short)",
                "status_short == -1",
            ],
            "command_argument_controls": ["call get_command_argument(1, value_number, length_number, status_number)"],
            "command_argument_values": ["call get_command_argument(n + 1, value=absent_value)"],
            "command_argument_numbering": ["n == 1 .and. status_first == 0"],
            "command_argument_zero": ["call get_command_argument(0, length=length_zero, status=status_zero)"],
            "command_argument_status": [
                "call get_command_argument(-1, status=status_negative)",
                "status_short == -1 .and. length_short == 5",
            ],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(source.count("! rule: "), 1)
            self.assertEqual(source.count("! covers: "), len(spec["facets"]))
            self.assertEqual(source.count("  implicit none\n"), 1)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertIn(f"if (checks /= {len(spec['facets'])})", source)
            self.assertNotIn("errmsg", source.lower())
            for needle in anchors[spec["variant"]]:
                self.assertIn(needle, source)
        self.assertNotIn("get_environment_variable(", "\n".join(spec["source"].lower() for spec in self.specs.values()))

    def test_feature_mutations_bind_complete_parent_sources_and_facets(self):
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 20)
        by_facet = {}
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            self.assertEqual({m["facet"] for m in spec["mutations"]}, set(spec["facets"]))
            hashes = set()
            for mutation in spec["mutations"]:
                mutant = generated.mutated_source(spec, mutation)
                self.assertNotEqual(mutant, raw)
                self.assertNotIn(generated.sha(mutant), hashes)
                hashes.add(generated.sha(mutant))
                self.assertEqual(mutation["kind"], "source")
                self.assertEqual(mutation["category"], "feature")
                by_facet.setdefault((spec["rule"], mutation["facet"]), set()).add(mutation["id"])
                expected = raw
                for start, end, old, new in reversed(mutation["spans"]):
                    self.assertEqual(raw[start:end].decode("ascii"), old)
                    expected = expected[:start] + new.encode("ascii") + expected[end:]
                self.assertEqual(mutant, expected)
        selected_facets = {(rule, facet) for rule, (_, facets) in generated.SELECTED.items() for facet in facets}
        self.assertEqual(set(by_facet), selected_facets)

    def test_catalogues_remove_only_selected_facets_and_regenerate_views(self):
        for section, catalogue_path in generated.CATALOGUES.items():
            catalogue = self.registry.catalogues[section]
            by_rule = {row["id"]: row for row in catalogue["requirements"]}
            for rule, (_, facets) in generated.SELECTED.items():
                if rule not in by_rule:
                    continue
                row = by_rule[rule]
                for facet in facets:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(generated.ORACLE_PREFIXES[rule], row["oracle"])
                self.assertIn(generated.LIMIT_PREFIXES[rule], row["oracle_limitation"])
            self.assertEqual(generated.synced_catalogue(catalogue), catalogue)
            view = generated.render_view(section, catalogue)
            if any(rule in by_rule for rule in generated.SELECTED):
                self.assertIn(generated.SUMMARY_BEGIN, view)
                self.assertIn("GET_ENVIRONMENT_VARIABLE absent-name facets remain pending", view)
            else:
                self.assertNotIn(generated.SUMMARY_BEGIN, view)
        self.assertNotIn("GET_COMMAND-command-assigned-entire-command-or-blanks",
                         self.registry.requirements["S16.9.92-002"].get("pending", {}))
        self.assertIn("GET_COMMAND_ARGUMENT-ERRMSG-default-character-scalar",
                      self.registry.requirements["S16.9.93-001"].get("pending", {}))
        self.assertNotIn("GET_COMMAND_ARGUMENT-status-positive-for-negative-number",
                         self.registry.requirements["S16.9.93-006"].get("pending", {}))
        self.assertIn("GET_ENVIRONMENT_VARIABLE-STATUS-one-for-nonexistence",
                      self.registry.requirements["S16.9.94-004"].get("pending", {}))
        self.assertIn("GET_ENVIRONMENT_VARIABLE-TRIM_NAME-logical-scalar",
                      self.registry.requirements["S16.9.94-001"].get("pending", {}))

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        self.assertEqual(generated.build_corpus()[0], self.files)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        before = {path: path.read_bytes() for path in self.files}
        generated.generate(ROOT, check=True)
        self.assertEqual({path: path.read_bytes() for path in self.files}, before)


if __name__ == "__main__":
    unittest.main()
