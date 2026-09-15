import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import run_tests as runner


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'derived_parameter_generator', ROOT / 'tools/generate_derived_parameter_fixtures.py')
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


class DerivedParameterFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = GENERATOR.build_corpus()
        cls.registry = runner.Registry()
        all_cases = runner.collect_cases(ROOT / 'tests', cls.registry)
        cls.cases = {case.name: case for case in all_cases if case.name in cls.corpus.cases}

    def contents(self, name):
        case = self.cases[name]
        return (case.fixture.root / 'source.f90').read_text() if case.fixture else Path(case.path).read_text()

    def diagnostic(self, case, message, family='lfortran', status=1, filename='source.f90', line=None):
        expected = case.fixture.expectation.diagnostic
        line = expected['line'] if line is None else line
        point = f'{line}-{line}:1-30' if family == 'lfortran' else f'{line}:1'
        severity = 'semantic error' if family == 'lfortran' else 'error'
        output = f'{filename}:{point}: {severity}: {message}'
        comp = runner.Compiler(family, family, 'f23' if family == 'lfortran' else 'f2023')
        return runner.judge_diagnostic(
            runner.ProcessResult(status, output), comp, case.rule, expected).outcome

    def test_exact_generated_case_set_and_declared_phases(self):
        self.assertEqual(len(self.cases), 66)
        self.assertEqual(set(self.cases), set(self.corpus.cases))
        self.assertEqual(sum(case.kind == 'invalid' for case in self.cases.values()), 11)
        self.assertEqual(sum(case.fixture is None for case in self.cases.values()), 27)
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assertEqual(case.rule, self.corpus.cases[name]['rule'])
                self.assertEqual(case.meta.facets, self.corpus.cases[name]['facets'])
                self.assertEqual(case.meta.standard, 'f2023')
                self.assertEqual(case.meta.profiles, [])
                if case.fixture:
                    self.assertEqual(case.fixture.expectation.phase, 'compile')
                    self.assertEqual(case.meta.evidence, 'effect' if case.kind == 'invalid' else 'positive-control')
                else:
                    self.assertEqual(case.meta.evidence, 'effect')

    def test_generator_matches_exact_inputs(self):
        for path, expected in self.corpus.files.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), expected)
                if path.suffix == '.f90':
                    self.assertLessEqual(max(map(len, expected.splitlines())), 132)

    def test_pending_matches_only_unimplemented_facets(self):
        coverage = self.corpus.coverage()
        total = 0
        for section in ('7.5.3.1', '7.5.3.2'):
            for requirement in self.registry.catalogues[section]['requirements']:
                self.assertEqual(set(requirement['pending']),
                                 set(requirement['facets']) - coverage.get(requirement['id'], set()))
                total += len(requirement['pending'])
        self.assertEqual(total, 11)
        self.assertIn('explicit-integer-carriers-canonical-use',
                      self.registry.requirements['S7.5.3.1-001']['pending'])
        self.assertIn('canonical-expression-categories', self.registry.requirements['R733']['pending'])

    def test_every_negative_has_its_source_minimal_repair(self):
        repairs = {
            'R732_invalid__parameter_comma': ('integer kind', 'integer, kind'),
            'R732_invalid__parameter_colons': ('integer, kind : tag', 'integer, kind :: tag'),
            'R732_invalid__parameter_integer_prefix': ('real, kind', 'integer, kind'),
            'R733_invalid__parameter_missing_default': ('width =', 'width = 3'),
            'C746_invalid__parameter_missing_header': ('type :: packet', 'type :: packet(tag)'),
            'C746_invalid__parameter_unlisted_kind': ('packet(tag)', 'packet(tag,extra)'),
            'C746_invalid__parameter_unlisted_len': ('packet(tag)', 'packet(tag,extra)'),
            'C747_invalid__parameter_missing_tag': (
                'integer, len :: width', 'integer, len :: width\ninteger, kind :: tag'),
            'C747_invalid__parameter_missing_width': (
                'integer, kind :: tag', 'integer, kind :: tag\ninteger, len :: width'),
            'C747_invalid__parameter_duplicate_list': ('tag, tag', 'tag'),
            'C747_invalid__parameter_duplicate_statement': (
                'integer, len :: width\ninteger, len :: width', 'integer, len :: width'),
        }
        self.assertEqual(set(repairs), {case.name for case in self.cases.values() if case.kind == 'invalid'})
        for name, (wrong, repair) in repairs.items():
            bad = self.contents(name)
            good = self.contents(name.replace('_invalid__', '_valid__') + '_repair')
            with self.subTest(case=name):
                self.assertEqual(bad.count(wrong), 1)
                self.assertEqual(bad.replace(wrong, repair, 1), good)

    def test_wrong_subject_and_recovery_messages_do_not_pass(self):
        wrong = [
            'type parameter definitions must appear before component declarations',
            'Symbol is already declared in the same scope',
            "Type parameter 'unrelated' was already declared in this derived type",
            "No definition found for type parameter 'unrelated'",
            "expected '::' in a procedure argument list",
            'Expected end of statement',
            'Syntax error in data declaration',
            'Invalid character in name',
        ]
        for case in self.cases.values():
            if case.kind != 'invalid':
                continue
            for message in wrong:
                for family in ('lfortran', 'gfortran', 'flang'):
                    for status in (0, 1):
                        with self.subTest(case=case.name, message=message, family=family, status=status):
                            self.assertEqual(self.diagnostic(case, message, family, status), 'fail')

    def test_causal_reports_require_the_declared_file_and_relation(self):
        for case in self.cases.values():
            if case.kind != 'invalid':
                continue
            expected = case.fixture.expectation.diagnostic
            message = expected['contains_any'][0]
            for family in ('lfortran', 'gfortran', 'flang'):
                with self.subTest(case=case.name, family=family):
                    self.assertEqual(self.diagnostic(case, message, family, 0), 'pass')
                    self.assertEqual(self.diagnostic(case, message, family, filename='other.f90'), 'fail')
                    self.assertEqual(self.diagnostic(case, message, family, line=1), 'fail')
                    self.assertEqual(self.diagnostic(case, 'Not yet implemented: ' + message, family), 'fail')
        duplicate = self.cases['C747_invalid__parameter_duplicate_statement']
        self.assertEqual(duplicate.fixture.expectation.diagnostic['line'], 5)
        self.assertNotIn('end_line', duplicate.fixture.expectation.diagnostic)

    def test_small_default_conversions_never_narrow_kind_identifiers(self):
        for category, value in (('kind', '-2'), ('len', '3')):
            selected = self.contents('S7_5_3_1_002_valid__' + category + '_default_to_selected')
            default = self.contents('S7_5_3_1_002_valid__' + category + '_selected_to_default')
            self.assertIn(f'integer(ik), {category} :: tag = {value}', selected)
            self.assertIn(f'integer, {category} :: tag = {value}_ik', default)
            for text in (selected, default):
                self.assertIn('selected_int_kind(18)', text)
                self.assertNotIn('tag = kind(', text)
                self.assertNotIn('stop 77', text)
                self.assertNotIn('packet()', text)

    def test_component_effects_guard_shapes_and_separate_parameter_values(self):
        for name in ('kind_component_bound', 'len_component_bound', 'mixed_parameters'):
            text = self.contents('S7_5_3_1_003_valid__' + name)
            self.assertLess(text.index('if (size(a%values)'), text.index('a%values ='))
            self.assertIn('if (any(a%values', text)
        text = self.contents('S7_5_3_1_003_valid__component_character')
        self.assertIn('if (len(a%text) /= 2 .or. len(b%text) /= 3)', text)
        self.assertIn("a%text = 'ab'", text)
        self.assertIn("b%text = 'xyz'", text)

    def test_constant_and_header_order_witnesses_have_distinct_premises(self):
        default = self.contents('S7_5_3_1_004_valid__dependent_default')
        self.assertLess(default.index('integer, kind :: tag'), default.index('integer, len :: extent'))
        self.assertIn('type(packet(tag=5))', default)
        order = self.contents('S7_5_3_2_001_valid__reversed_statements')
        self.assertIn('type :: packet(left,right)', order)
        self.assertLess(order.index('integer, kind :: right'), order.index('integer, kind :: left'))
        inherited = self.contents('S7_5_3_2_002_valid__inherited_only')
        self.assertIn('type, extends(parent) :: child\nend type', inherited)
        self.assertIn('type(child(2,3))', inherited)
        self.assertNotIn('extends(parent(', inherited)

    def test_reference_column_ranges_remain_single_line_locations(self):
        message = "Component 'tag' at (1) already declared at (2)"
        good = f'source.f90:4:20-25:\nError: {message}\n'
        self.assertEqual(runner.reference_error_lines(good, messages=[message]), {4})
        self.assertEqual(runner.reference_error_lines(good, 'source.f90', [message]), {4})
        self.assertEqual(runner.reference_error_lines(good, 'other.f90', [message]), set())
        for columns in ('25-20', '0-25', '5-', '5--8', '5-x', '5-8-9'):
            text = f'source.f90:3:1:\nsource.f90:4:{columns}:\nError: {message}\n'
            self.assertEqual(runner.reference_error_lines(text, 'source.f90', [message]), set())
        self.assertEqual(runner.reference_error_lines(
            f'source.f90:4-5:20-25: Error: {message}', 'source.f90', [message]), set())

    def test_c747_duplicate_report_cannot_borrow_a_previous_location(self):
        case = self.cases['C747_invalid__parameter_duplicate_statement']
        expected = case.fixture.expectation.diagnostic
        message = "Component 'width' at (1) already declared at (2)"
        for family in ('gfortran', 'flang'):
            comp = runner.Compiler(family, family, 'f2023')
            for status in (0, 1):
                for origin in ('source.f90', 'other.f90'):
                    for columns in ('5-', '5--8', '5-x', '5-8-9'):
                        with self.subTest(family=family, status=status, origin=origin, columns=columns):
                            output = f'source.f90:5:1:\n{origin}:9:{columns}:\nError: {message}\n'
                            result = runner.judge_diagnostic(
                                runner.ProcessResult(status, output), comp, case.rule, expected)
                            self.assertEqual(result.outcome, 'fail')

    def test_c747_severity_named_foreign_files_cannot_supply_the_expected_report(self):
        case = self.cases['C747_invalid__parameter_duplicate_statement']
        expected = case.fixture.expectation.diagnostic
        message = "Component 'width' at (1) already declared at (2)"
        for family in ('gfortran', 'flang'):
            comp = runner.Compiler(family, family, 'f2023')
            for status in (0, 1):
                for origin in ('Error', 'Fatal Error', 'Warning', 'portability',
                               'Error:asset', 'Error: asset', "Error: 'asset'", "Error: can't"):
                    for columns in ('1', '1-9', '5-', '5--8', '5-x', '5-8-9'):
                        with self.subTest(family=family, status=status, origin=origin, columns=columns):
                            output = f'source.f90:5:1:\n{origin}:9:{columns}: Error: {message}\n'
                            result = runner.judge_diagnostic(
                                runner.ProcessResult(status, output), comp, case.rule, expected)
                            self.assertEqual(result.outcome, 'fail')

    def test_c747_mixed_coordinates_never_qualify_quoted_locations(self):
        case = self.cases['C747_invalid__parameter_duplicate_statement']
        expected = case.fixture.expectation.diagnostic
        message = "Component 'width' at (1) already declared at (2)"
        quoted = f'Error: "/tmp/source.f90:5:1: Error: {message}"'
        for family in ('gfortran', 'flang'):
            comp = runner.Compiler(family, family, 'f2023')
            for status in (0, 1):
                for prefix in ('', 'source.f90:4:1:\n'):
                    for columns in ('1', '1-9', '5-', '5--8', '5-x', '5-8-9'):
                        with self.subTest(family=family, status=status, prefix=prefix, columns=columns):
                            output = prefix + quoted + f' other.f90:9:{columns}:\n'
                            result = runner.judge_diagnostic(
                                runner.ProcessResult(status, output), comp, case.rule, expected)
                            self.assertEqual(result.outcome, 'fail')
                            self.assertEqual(result.output, output)

    def test_staged_c747_mixed_coordinates_do_not_create_diagnostic_evidence(self):
        case = self.cases['C747_invalid__parameter_duplicate_statement']
        message = "Component 'width' at (1) already declared at (2)"
        outputs = []
        for family in ('gfortran', 'flang'):
            comp = runner.Compiler(family, family, 'f2023')
            for status in (0, 1):
                def process(command, cwd, timeout, stdin=None):
                    output = (f'Error: "{Path(cwd) / "source.f90"}:5:1: Error: {message}"'
                              ' other.f90:9:5-:\n')
                    outputs.append(output)
                    return runner.ProcessResult(status, output)
                with self.subTest(family=family, status=status):
                    with patch.object(runner, 'run', side_effect=process):
                        result = runner.check_fixture(case.fixture, comp)
                    self.assertEqual(result.outcome, 'fail')
                    self.assertEqual(result.output, outputs[-1])
                    self.assertEqual(result.input_hashes, {
                        'source.f90': runner.hashlib.sha256(
                            (case.fixture.root / 'source.f90').read_bytes()).hexdigest()})


if __name__ == '__main__':
    unittest.main()
