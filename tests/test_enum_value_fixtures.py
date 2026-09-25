"""Independent enum sequence/partition models and generated observer bindings."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import run_tests as runner
from suite_data import Registry

import generate_enum_value_fixtures as generated
import generate_enum_type_fixtures as enum_type


EXPECTED = {
    "common": [0, 1, 4, 5, 9, 10],
    "flat": [0, 1, 4, 5, 9, 10, 4, 5],
    "split": [0, 1, 4, 5, 9, 10, 4, 5],
    "negative": [-3, -2, 4, 4, 5],
    "fresh": [0, 1],
}
PARTITIONS = {"common": [3, 3], "flat": [8], "split": [3, 5], "negative": [2, 3], "fresh": [2]}


def parse_enums(source):
    definitions = []
    for block in re.findall(r"(?ms)^enum, bind\(c\)\n(.*?)^end enum$", source):
        statements, names, initializers = [], [], []
        for line in block.splitlines():
            match = re.fullmatch(r"enumerator\s*(?:::)?\s+(.+)", line)
            if not match:
                raise AssertionError("unexpected finite enum source line: " + line)
            entries = []
            for entry in match[1].split(","):
                name, separator, value = entry.strip().partition("=")
                if not re.fullmatch(r"[a-z][a-z_0-9]*", name):
                    raise AssertionError("unexpected enumerator name")
                entries.append((name, int(value) if separator else None))
                names.append(name)
                initializers.append(int(value) if separator else None)
            statements.append(entries)
        definitions.append(dict(names=names, initializers=initializers, statements=statements))
    return definitions


def source_values(statements, restart_at_statement=False, previous=None, ignore_explicit=False):
    result = []
    for statement in statements:
        if restart_at_statement:
            previous = None
        for name, explicit in statement:
            if explicit is not None and not ignore_explicit:
                previous = explicit
            else:
                previous = 0 if previous is None else previous + 1
            result.append(previous)
    return result


class EnumValueFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs, cls.specs = generated.build_corpus()
        cls.registry = Registry(ROOT)
        all_cases = runner.collect_cases(ROOT / "tests", cls.registry)
        cls.cases = {c.name: c for c in all_cases if "/fixtures/enum_value_" in c.path}
        cls.catalogue = cls.registry.catalogues[generated.SECTION]

    def sources(self):
        for name, spec in self.specs.items():
            yield name, spec, (self.cases[name].fixture.root / spec["source_file"]).read_text()

    def test_exact_shared_case_ids_metadata_and_runtime_phases(self):
        self.assertEqual(set(self.specs), {
            "S7_6_1_001_valid__enum_value_common_kind",
            "S7_6_1_004_valid__enum_value_sequence_matrix",
        })
        self.assertEqual(set(self.cases), set(self.specs))
        self.assertEqual(sum(len(s["definitions"]) for s in self.specs.values()), 5)
        self.assertEqual(sum(len(g["names"]) for s in self.specs.values() for g in s["definitions"]), 29)
        for name, case in self.cases.items():
            self.assertEqual(case.kind, "valid")
            self.assertEqual(case.fixture.expectation.phase, "run")
            self.assertEqual(case.fixture.expectation.outcome, "success")
            self.assertEqual(case.fixture.expectation.exit_code, 0)
            self.assertTrue(case.fixture.link)
            self.assertEqual(case.meta.evidence, "effect")
            self.assertEqual(self.registry.requirements[case.rule]["category"], "effect")
            self.assertEqual(case.meta.standard, "f2023")
            self.assertEqual(case.meta.oracle_basis, "standard")
            self.assertEqual(case.meta.images, 1)
            self.assertFalse(case.meta.profiles)
            self.assertFalse(case.meta.coarray)
        selected = runner.select_cases(list(self.cases.values()), sorted(self.cases))
        self.assertEqual({c.name for c in selected}, set(self.cases))

    def test_exact_generated_files_and_no_extra_source_forms(self):
        actual = {p for p in (ROOT / "tests/fixtures").glob("enum_value_*/*") if p.is_file()}
        self.assertEqual(set(self.outputs), actual)
        self.assertEqual(len(actual), 4)
        for path, data in self.outputs.items():
            self.assertEqual(path.read_bytes(), data)
            data.decode("ascii")
            if path.suffix == ".f90":
                self.assertLessEqual(max(map(len, data.splitlines())), 132)
        for name, spec, source in self.sources():
            self.assertNotRegex(source, r"(?i)enum,\s*bind\(c\)\s*::")
            self.assertNotIn("enumeration type", source.lower())
            self.assertNotRegex(source, r"(?im)^type\b")
            self.assertNotRegex(source, r"(?i)\b(?:selected_int_kind|c_int|transfer|storage_size|huge|next)\b")
            self.assertNotIn("integer(", source.lower())
            self.assertNotRegex(source, r"(?i)\b[boz]['\"]")
            self.assertNotIn("stop 77", source)
            self.assertNotIn("skip", source.lower())
            self.assertEqual(source.split("program enum_values\n")[0], generated.OBSERVER)

    def test_independent_source_sequence_and_statement_partition(self):
        seen = set()
        for name, spec, source in self.sources():
            parsed = parse_enums(source)
            self.assertEqual(len(parsed), len(spec["definitions"]))
            all_names = [n for definition in parsed for n in definition["names"]]
            self.assertEqual(len(all_names), len(set(all_names)))
            for definition, oracle in zip(parsed, spec["definitions"]):
                label = oracle["label"]
                seen.add(label)
                self.assertEqual(source_values(definition["statements"]), EXPECTED[label])
                self.assertEqual([len(s) for s in definition["statements"]], PARTITIONS[label])
                self.assertEqual(oracle["expected"], EXPECTED[label])
                self.assertEqual(definition["names"], oracle["names"])
                self.assertEqual(definition["initializers"], oracle["initializers"])
        self.assertEqual(seen, set(EXPECTED))

    def test_every_runtime_observation_is_bound_to_actual_source_and_literal_oracle(self):
        for name, spec, source in self.sources():
            self.assertEqual(source.count("call check_definition("), len(spec["definitions"]))
            for group, binding in zip(spec["definitions"], spec["observation_bindings"]):
                block = "\n".join(source.splitlines()[binding["line"]-1:binding["end_line"]]) + "\n"
                self.assertEqual(block, generated.observation_source(group))
                self.assertEqual(hashlib.sha256(block.encode()).hexdigest(), binding["sha256"])
                flattened = re.sub(r"\s|&", "", block)
                expected = "[" + ",".join(map(str, EXPECTED[group["label"]])) + "]"
                self.assertIn(expected, flattened)
                self.assertEqual(re.findall(r"int\((\w+)\)", block), group["names"])
                kind_names = re.findall(r"kind\((\w+)\)", block)
                self.assertEqual(kind_names[:-1], group["names"])
                self.assertEqual(kind_names[-1], group["names"][0])
                self.assertIn("==kind(" + group["names"][0] + ")", flattened)
                missing = source.replace(block, "", 1)
                self.assertEqual(missing.count("call check_definition("), len(spec["definitions"])-1)
                self.assertNotEqual(missing.encode(), self.outputs[self.cases[name].fixture.root / spec["source_file"]])

    def test_explicit_values_are_not_ordinals_and_defaults_follow_previous_value(self):
        for name, spec, source in self.sources():
            for parsed, group in zip(parse_enums(source), spec["definitions"]):
                expected = EXPECTED[group["label"]]
                actual = source_values(parsed["statements"])
                self.assertTrue(generated.observer_accepts(actual, ["opaque-kind"] * len(actual), expected))
                if group["label"] != "fresh":
                    ordinal = list(range(1, len(actual)+1))
                    self.assertFalse(generated.observer_accepts(ordinal, ["opaque-kind"] * len(actual), expected))
                    implicit_only = source_values(parsed["statements"], ignore_explicit=True)
                    self.assertFalse(generated.observer_accepts(implicit_only, ["opaque-kind"] * len(actual), expected))
                if group["label"] in ("common", "split"):
                    restarted = source_values(parsed["statements"], restart_at_statement=True)
                    self.assertEqual(restarted[3], 0)
                    self.assertEqual(expected[3], 5)
                    self.assertFalse(generated.observer_accepts(restarted, ["opaque-kind"] * len(actual), expected))
        self.assertEqual(EXPECTED["flat"][-4:], [9, 10, 4, 5])
        self.assertEqual(EXPECTED["negative"], [-3, -2, 4, 4, 5])

    def test_both_wrong_partition_variants_cannot_cancel(self):
        wrong = [1, 2, 4, 5, 9, 10, 4, 5]
        self.assertEqual(wrong, list(wrong))
        for label in ("flat", "split"):
            self.assertFalse(generated.observer_accepts(wrong, ["kind"] * 8, EXPECTED[label]))
        flat_kind, split_kind = object(), object()
        self.assertTrue(generated.observer_accepts(EXPECTED["flat"], [flat_kind] * 8, EXPECTED["flat"]))
        self.assertTrue(generated.observer_accepts(EXPECTED["split"], [split_kind] * 8, EXPECTED["split"]))
        self.assertIsNot(flat_kind, split_kind)

    def test_new_definition_restarts_zero_without_reusing_constant_names(self):
        spec = self.specs["S7_6_1_004_valid__enum_value_sequence_matrix"]
        source = (self.cases["S7_6_1_004_valid__enum_value_sequence_matrix"].fixture.root /
                  spec["source_file"]).read_text()
        parsed = parse_enums(source)
        negative, fresh = parsed[-2:]
        self.assertEqual(source_values(negative["statements"])[-1], 5)
        self.assertTrue(all(x is None for x in fresh["initializers"]))
        self.assertEqual(source_values(fresh["statements"]), [0, 1])
        leaking_previous = source_values(fresh["statements"], previous=5)
        self.assertEqual(leaking_previous, [6, 7])
        self.assertFalse(generated.observer_accepts(leaking_previous, ["fresh-kind"] * 2, [0, 1]))
        self.assertFalse(set(negative["names"]) & set(fresh["names"]))

    def test_every_value_and_kind_cell_has_an_independent_countermodel(self):
        value_probes = kind_probes = 0
        for expected in EXPECTED.values():
            kinds = ["local-kind"] * len(expected)
            self.assertTrue(generated.observer_accepts(expected, kinds, expected))
            for i, value in enumerate(expected):
                changed = list(expected)
                changed[i] = 0 if value != 0 else 1
                self.assertFalse(generated.observer_accepts(changed, kinds, expected))
                value_probes += 1
                changed_kinds = list(kinds)
                changed_kinds[i] = "different-kind"
                self.assertFalse(generated.observer_accepts(expected, changed_kinds, expected))
                kind_probes += 1
            for i, j in itertools.combinations(range(len(expected)), 2):
                changed = list(expected)
                changed[i], changed[j] = changed[j], changed[i]
                self.assertEqual(generated.observer_accepts(changed, kinds, expected),
                                 expected[i] == expected[j])
            self.assertFalse(generated.observer_accepts(expected[:-1], kinds[:-1], expected))
            self.assertFalse(generated.observer_accepts(expected + [0], kinds + ["local-kind"], expected))
            self.assertFalse(generated.observer_accepts(expected, kinds[:-1], expected))
        self.assertEqual((value_probes, kind_probes), (29, 29))
        self.assertFalse(generated.observer_accepts([], [], []))

    def test_observer_shape_and_boolean_guards_precede_unsafe_operations(self):
        observer = generated.OBSERVER
        self.assertLess(observer.index("size(actual)/=size(expected)"), observer.index("any(actual/=expected)"))
        self.assertLess(observer.index("size(actual)==0"), observer.index("any(actual/=expected)"))
        self.assertIn("if (.not.kind_agrees) then", observer)
        self.assertIn("ENUM_VALUE_MISMATCH", observer)
        self.assertIn("ENUM_KIND_MISMATCH", observer)
        self.assertNotIn("save", observer.lower())
        self.assertNotIn("kind_agrees=", observer)

    def test_source_identities_and_all_unselected_pending_plans(self):
        keys = ["id", "title", "source", "source_units", "category", "diagnostic_obligation",
                "definition", "facets", "dependencies"]
        protected = {k: self.catalogue[k] for k in ("subunits", "accounting")}
        protected["requirements"] = [{k: r[k] for k in keys if k in r} for r in self.catalogue["requirements"]]
        self.assertEqual(hashlib.sha256(json.dumps(protected, sort_keys=True).encode()).hexdigest(),
                         "ebb266eaf26ade827daa2b6f494e39249b9129ebbfea81d8e3f4762d14f42449")
        self.assertEqual(len(self.catalogue["requirements"]), 15)
        self.assertEqual(len(self.catalogue["accounting"]), 116)
        self.assertEqual(sum(map(len, self.catalogue["subunits"].values())), 93)
        self.assertEqual(sum(len(r["facets"]) for r in self.catalogue["requirements"]), 64)
        self.assertEqual(sum(len(r["pending"]) for r in self.catalogue["requirements"]), 35)
        coverage = {}
        for case in self.cases.values():
            coverage.setdefault(case.rule, set()).update(case.meta.facets)
        self.assertEqual(coverage, {r: set(f) for r, f in generated.ELIGIBLE.items()})
        shared = enum_type.union_coverage()
        for r in self.catalogue["requirements"]:
            self.assertEqual(set(r["pending"]), set(r["facets"]) - shared.get(r["id"], set()))

    def test_full_view_pending_appendix_and_admin_preserving_states(self):
        view = (ROOT / generated.VIEW).read_text()
        self.assertEqual(view, generated.render_view(self.catalogue, self.specs))
        appendix = view.split("## Complete finite pending plans\n", 1)[1].split(
            "## Reproduction and separate gates", 1)[0]
        self.assertEqual(appendix.count("* **`"), 35)
        for r in self.catalogue["requirements"]:
            for facet, plan in r["pending"].items():
                self.assertIn(f"* **`{facet}`** - {plan}", appendix)
        self.assertEqual(generated.synced_catalogue(self.catalogue, self.specs), self.catalogue)
        reviewed = copy.deepcopy(self.catalogue)
        reviewed["review_state"] = "reviewed"
        reviewed["review_rationale"] = "In-memory administrative state, not an approval."
        r = Registry(ROOT)
        r.catalogues[generated.SECTION] = reviewed
        reviewed["review_fingerprint"] = r.catalogue_fingerprint(generated.SECTION)
        self.assertEqual(generated.synced_catalogue(reviewed, self.specs), reviewed)
        self.assertIn("Catalogue source review: reviewed.", generated.render_view(reviewed, self.specs))
        reviewed["review_fingerprint"] = "0" * 64
        self.assertIn("Catalogue source review: stale.", generated.render_view(reviewed, self.specs))


if __name__ == "__main__":
    unittest.main()
