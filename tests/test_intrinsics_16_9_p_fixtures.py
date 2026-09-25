"""Generated runtime fixtures for Fortran 2023 intrinsic procedures 16.9.121-16.9.127."""

import json
from pathlib import Path
import re
import sys
import unittest
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import run_tests as runner
from suite_data import Registry, SuiteError, validate_case_requirement

sys.path.insert(0, str(ROOT / "tools"))
import generate_intrinsics_16_9_p_fixtures as generated


class Intrinsics169PFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.specs = generated.build_corpus(ROOT)
        cls.registry = Registry(ROOT)
        cls.all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        manifests = {path for path in cls.files if path.name == "fixture.json"}
        cls.cases = {case.name: case for case in cls.all_cases if Path(case.path) in manifests}

    def test_generated_inventory_and_metadata(self):
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(len(self.cases), 23)
        self.assertEqual(len(self.files), 46)
        self.assertEqual(sum(len(spec["facets"]) for spec in self.specs.values()), 53)
        self.assertEqual(sum(len(spec["mutations"]) for spec in self.specs.values()), 55)
        self.assertEqual(json.loads(json.dumps(self.specs)), self.specs)
        for name, case in self.cases.items():
            spec = self.specs[name]
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.rule, spec["rule"])
            self.assertEqual(case.meta.facets, spec["facets"])
            self.assertEqual((case.meta.evidence, case.meta.standard), (spec["evidence"], "f2023"))
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.coarray or case.meta.reference_warnings)
            self.assertEqual(case.meta.profiles, spec["profiles"])
            self.assertEqual(case.fixture.files, ["source.f90"])
            self.assertEqual(case.fixture.expectation.stdout, [spec["completion"]])
            self.assertEqual(case.fixture.expectation.stderr, [""])
            requirement = self.registry.requirements[case.rule]
            validate_case_requirement(case, requirement)
            with self.assertRaises(SuiteError):
                validate_case_requirement(replace(case, meta=replace(case.meta, facets=[])), requirement)

    def test_sources_are_source_derived_and_bounded(self):
        required = {
            "leadz_values": ["bit_size(zero)", "bit_size(one) - 1", "ibset(0, bit_size(0) - 1)", "leadz(not(0))"],
            "leadz_result_kind": ["kind(leadz(one)) == kind(0)"],
            "len_characteristics": ["rank(len(words))", "kind(len(words, kind=wide_kind))"],
            "len_values": ["character(len=0) :: empty", "allocate(character(len=7) :: allocated_s)", "pointer_s => target_s"],
            "len_trim_values": ["len_trim(trailing) == 2", "len_trim(internal) == 3", "len_trim(blanks) == 0"],
            "lge_ascii_order": ["lge(upper_a, digit)", "lge(lower_a, upper_z)", "lge(underscore, upper_z)"],
            "lgt_ascii_order": ["lgt(upper_a, digit)", "lgt(eq_a, eq_b)", "lgt(digit, upper_a)"],
            "lle_ascii_values": ["len(short_a) == 1", "lle(eq_a, eq_b)", "lle(digit, upper_a)"],
            "llt_ascii_values": ["len(short_a) == 1", "llt(eq_a, eq_b)", "llt(digit, upper_a)"],
        }
        for spec in self.specs.values():
            source = spec["source"]
            source.encode("ascii")
            self.assertNotIn("\r", source)
            self.assertLessEqual(max(map(len, source.splitlines())), 132)
            self.assertEqual(len(re.findall(r"(?m)^program ", source)), 1)
            self.assertEqual(len(re.findall(r"(?m)^end program ", source)), 1)
            self.assertIn("  implicit none\n", source)
            self.assertEqual(source.count(spec["completion"].rstrip()), 1)
            self.assertNotRegex(source.lower(), r"transfer\s*\(|loc\s*\(|c_loc\s*\(|sync\s+all")
            if spec["variant"].endswith("ascii_values") or spec["variant"].endswith("ascii_order"):
                self.assertNotRegex(source, r"[^\x00-\x7f]")
            for token in required.get(spec["variant"], []):
                self.assertIn(token, source)

    def test_mutations_are_complete_parent_feature_spans(self):
        seen_hashes = set()
        for spec in self.specs.values():
            raw = spec["source"].encode("ascii")
            self.assertEqual(generated.sha(raw), spec["source_sha256"])
            features = [mutation for mutation in spec["mutations"] if mutation["kind"] == "feature"]
            self.assertGreaterEqual(len(features), len(spec["facets"]))
            for mutation in spec["mutations"]:
                start, end = mutation["span"]
                self.assertEqual(raw[start:end].decode("ascii"), mutation["expected"])
                mutant = generated.mutate_source(spec, mutation)
                self.assertEqual(mutant, raw[:start] + mutation["replacement"].encode("ascii") + raw[end:])
                self.assertNotEqual(mutant, raw)
                digest = generated.sha(mutant)
                self.assertNotIn(digest, seen_hashes)
                seen_hashes.add(digest)

    def test_catalogues_remove_only_generated_target_facets(self):
        covered = {}
        for spec in self.specs.values():
            covered.setdefault(spec["rule"], set()).update(spec["facets"])
        for section in generated.SECTIONS:
            catalogue = self.registry.catalogues[section]
            expected = generated.sync_catalogue(section, catalogue, self.specs)
            self.assertEqual(expected, catalogue)
            view = generated.render_view(section, catalogue, ROOT)
            self.assertIn(generated.SUMMARY_BEGIN.format(section=section), view)
            for requirement in catalogue["requirements"]:
                if requirement["id"].startswith("S" + section + "-"):
                    missing = set(requirement["facets"]) - covered.get(requirement["id"], set())
                    self.assertEqual(missing, set(requirement.get("pending", {})), requirement["id"])
            for spec in self.specs.values():
                if spec["section"] != section:
                    continue
                row = self.registry.requirements[spec["rule"]]
                for facet in spec["facets"]:
                    self.assertNotIn(facet, row.get("pending", {}))
                self.assertIn(f"{spec['rule']} {generated.TOPIC} runtime fixture: ", row["oracle"])

    def test_non_ascii_processor_dependent_facets_stay_pending(self):
        expected = {
            "S16.9.124-004": {"LGE-non-ASCII-result-processor-dependent"},
            "S16.9.125-004": {"LGT-non-ASCII-result-processor-dependent"},
            "S16.9.126-004": {"LLE-non-ASCII-result-processor-dependent"},
            "S16.9.127-004": {"LLT-non-ASCII-result-processor-dependent"},
        }
        for rule, facets in expected.items():
            self.assertEqual(set(self.registry.requirements[rule].get("pending", {})), facets)

    def test_generation_is_deterministic_and_check_mode_read_only(self):
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)
        generated.generate(ROOT, check=True)
        for path, raw in self.files.items():
            self.assertEqual(path.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
