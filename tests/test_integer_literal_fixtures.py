"""Independent regression oracles for the bounded intrinsic/integer fixtures."""
from pathlib import Path
import re
import unittest

import run_tests as runner


class IntegerLiteralCorpusTests(unittest.TestCase):
    root = Path(__file__).resolve().parent

    @classmethod
    def setUpClass(cls):
        paths = sorted((cls.root / 'fixtures').glob('intrinsic_type_spec_*/fixture.json'))
        paths += sorted((cls.root / 'fixtures').glob('integer_literal_*/fixture.json'))
        fixtures = [runner.load_fixture(path, runner.PROFILES) for path in paths]
        cls.negatives = {fixture.name: fixture for fixture in fixtures if fixture.kind == 'invalid'}
        cls.controls = {fixture.name: fixture for fixture in fixtures if fixture.kind == 'valid'}
        cls.messages = {
            'R706_invalid__missing_value': [
                "Token ')' is unexpected here", 'Expected initialization expression at (1)', "expected ')'"],
            'R706_invalid__wrong_keyword': ['Missing right parenthesis at (1)', "expected ')'"],
            'R707_invalid__double_sign': ['Syntax error in DATA statement at (1)', "expected '('"],
            'R708_invalid__empty_suffix': [
                "Token '_' (of type 'identifier') is unexpected here",
                'Missing kind-parameter at (1)', "expected '/'"],
            'R709_invalid__expression_suffix': [
                "Token '_' (of type 'identifier') is unexpected here",
                'Missing kind-parameter at (1)', "expected '/'"],
            'R710_invalid__double_exponent_sign': [
                "Token 'd' (of type 'identifier') is unexpected here",
                'Missing exponent in real number at (1)'],
            'R711_invalid__nondigit': [
                "Token 'a2' (of type 'identifier') is unexpected here",
                'Syntax error in DATA statement at (1)', "expected '/'"],
            'C718_invalid__variable_name': ['Must be a constant value'],
            'C718_invalid__real_name': [
                "Variable 'selector' is constant but not an integer",
                'Must have INTEGER type, but is REAL(8)'],
            'C719_invalid__negative_name': ['INTEGER(KIND=-1) is not a supported type'],
            'C720_invalid__absent_digit': [
                'Integer kind 0 at (1) not available', 'INTEGER(KIND=0) is not a supported type'],
            'C720_invalid__absent_name': [
                'Integer kind 0 at (1) not available', 'INTEGER(KIND=0) is not a supported type'],
        }
        for category in ('integer', 'real', 'complex', 'logical'):
            for variant, value in (('negative', -1), ('absent_zero', 0)):
                cls.messages[f'C717_invalid__{category}_{variant}'] = [
                    f'Kind {value} not supported for type {category.upper()} at (1)',
                    f'{category.upper()}(KIND={value}) is not a supported type',
                    f'Kind {value} is not supported for {category.title()}',
                ]

    def output(self, fixture, message, family='lfortran', file='source.f90', first=None, last=None):
        line = fixture.expectation.diagnostic['line']
        first = line if first is None else first
        last = first if last is None else last
        if family == 'lfortran':
            return f'{file}:{first}-{last}:1-60: semantic error: {message}\n'
        return f'{file}:{first}:1: error: {message}\n'

    def judge(self, fixture, output, family='lfortran', status=1, timed_out=False):
        compiler = runner.Compiler(family, family, 'f23' if family == 'lfortran' else 'f2018')
        return runner.judge_diagnostic(
            runner.ProcessResult(status, output, timed_out=timed_out),
            compiler, fixture.rule, fixture.expectation.diagnostic).outcome

    def test_every_negative_rejects_its_independent_review_counterexample(self):
        messages = {
            'R706': 'Kind selectors are not supported',
            'C717': 'Kind parameter syntax is not supported',
            'C718': 'Integer constant is too large for its kind',
            'C719': 'Kind parameter syntax is not supported',
            'C720': 'Kind parameter syntax is not supported',
            'R707': 'Invalid kind parameter',
            'R708': 'Invalid kind parameter: literal kind suffix syntax is not supported',
            'R709': 'Invalid kind parameter: literal kind suffix syntax is not supported',
            'R710': 'Exponent is outside the representable range',
            'R711': 'Invalid kind parameter',
        }
        self.assertEqual(len(self.negatives), 20)
        for name, fixture in self.negatives.items():
            for status in (0, 1):
                with self.subTest(case=name, status=status):
                    output = self.output(fixture, messages[fixture.rule])
                    self.assertEqual(self.judge(fixture, output, status=status), 'fail')

    def test_negative_selector_does_not_credit_the_current_constancy_fallback(self):
        message = ('Only Integer literals or expressions which reduce to constant Integer '
                   'are accepted as kind parameters')
        for category in ('integer', 'real', 'complex', 'logical'):
            name = f'C717_invalid__{category}_negative'
            fixture = self.negatives[name]
            with self.subTest(case=name):
                self.assertEqual(self.judge(fixture, self.output(fixture, message)), 'fail')

    def test_specific_language_reports_are_preserved(self):
        self.assertEqual(set(self.messages), set(self.negatives))
        for name, messages in self.messages.items():
            fixture = self.negatives[name]
            for message in messages:
                for family in ('lfortran', 'gfortran', 'flang'):
                    with self.subTest(case=name, family=family, message=message):
                        output = self.output(fixture, message, family)
                        self.assertEqual(self.judge(fixture, output, family), 'pass')

    def test_missing_suffix_is_not_a_constant_type_or_value_cause(self):
        for name in ('C718_invalid__variable_name', 'C718_invalid__real_name',
                     'C719_invalid__negative_name'):
            fixture = self.negatives[name]
            with self.subTest(case=name):
                output = self.output(fixture, 'Missing kind-parameter at (1)', 'gfortran')
                self.assertEqual(self.judge(fixture, output, 'gfortran'), 'fail')

    def test_causal_words_do_not_override_implementation_or_location_failures(self):
        for name, fixture in self.negatives.items():
            message = self.messages[name][0]
            line = fixture.expectation.diagnostic['line']
            good = self.output(fixture, message)
            for output in (
                    self.output(fixture, 'Not yet implemented: ' + message),
                    self.output(fixture, 'Unsupported feature: ' + message),
                    self.output(fixture, message, file='other.f90'),
                    self.output(fixture, message, first=line - 1, last=line),
                    self.output(fixture, 'Unrelated error') + f'  {line} | {message}\n',
                    good + '\nASR verify pass error\n',
                    good + '\nLLVM ERROR: broken IR\n',
                    good + '\nerror: out of memory\n'):
                with self.subTest(case=name, output=output):
                    self.assertEqual(self.judge(fixture, output), 'fail')
            for status, timed_out in ((-11, False), (139, False), (1, True)):
                with self.subTest(case=name, status=status, timed_out=timed_out):
                    self.assertEqual(self.judge(fixture, good, status=status, timed_out=timed_out), 'fail')

    def test_integer_expression_kind_conversion_has_a_separate_qualified_case(self):
        unqualified = (self.root / 'clause07/R706_valid.f90').read_text()
        self.assertNotIn('! profile:', unqualified)
        self.assertIn('! covers: positional-expression keyword-expression\n', unqualified)
        self.assertIn('integer, parameter :: selector = kind(0)', unqualified)
        self.assertNotIn('selected_int_kind', unqualified.lower())
        qualified = (self.root / 'clause07/R706_valid__selected_expression_kind.f90').read_text()
        self.assertIn('! covers: integer-expression-kind\n', qualified)
        self.assertIn('! profile: integer-literal-kind-code-decimal10\n', qualified)
        self.assertIn('! standard: f2023\n', qualified)
        self.assertIn('integer(wide), parameter :: selector = kind(0)', qualified)
        profile = (self.root / 'profiles/integer_literal_kind_code_decimal10.f90').read_text()
        self.assertIn('reduced = kind(0)', profile)
        self.assertIn('do i = 1, 10', profile)
        self.assertIn('reduced = reduced / 10', profile)
        self.assertIn('if (reduced /= 0) stop 77', profile)
        self.assertNotIn('selected_int_kind', profile.lower())
        self.assertLess(10 ** 10 - 1, 10 ** 18 - 1)
        self.assertGreater(10 ** 20, 2 ** 63 - 1)

    def test_mandatory_integer_capacity_is_not_an_optional_profile(self):
        for name in ('S7_4_3_1_003_valid', 'S7_4_3_1_005_valid__mandatory_wide',
                     'S7_4_3_1_004_valid'):
            source = (self.root / f'clause07/{name}.f90').read_text()
            with self.subTest(case=name):
                self.assertNotIn('! profile:', source)
                self.assertNotRegex(source.lower(), r'\bstop\s+77\b')
        inventory = (self.root / 'profiles/integer_literal_bounded_inventory.f90').read_text()
        self.assertIn('if (selected_int_kind(18) < 0) error stop 3', inventory)
        self.assertIn('if (size(integer_kinds) > 16) stop 77', inventory)

    def test_actual_boundary_tokens_match_independent_integer_arithmetic(self):
        branches = {'range2_binary7': 7, 'range4_binary15': 15, 'default_binary31': 31,
                    'range18_binary63': 63, 'range38_binary127': 127}
        for branch, bits in branches.items():
            limit = sum(2 ** power for power in range(bits))
            suffix = '' if branch == 'default_binary31' else '_k'
            for requirement in ('005', '007'):
                path = self.root / f'clause07/S7_4_3_1_{requirement}_valid__{branch}.f90'
                raw = path.read_bytes()
                values = dict(re.findall(rb'data\s+(\w+)\s*/([^/]+)/', raw, re.I))
                expected = ({'upper': limit, 'adjacent': limit - 1, 'positive': limit, 'lower': -limit}
                            if requirement == '005' else {'positive': limit, 'negative': -limit})
                self.assertEqual(set(values), {key.encode() for key in expected})
                for name, value in expected.items():
                    token = values[name.encode()].decode('ascii')
                    with self.subTest(branch=branch, requirement=requirement, value=name):
                        self.assertTrue(token.endswith(suffix))
                        digits = token[:-len(suffix)] if suffix else token
                        self.assertEqual(int(digits, 10), value)
                        if requirement == '007':
                            self.assertEqual(len(digits.lstrip('+-')) - len(str(abs(value))), 48)
                self.assertLessEqual(max(map(len, raw.splitlines())), 132)
            profile = (self.root / f'profiles/integer_literal_{branch}.f90').read_text()
            self.assertIn('if (radix(0_k) /= 2) stop 77', profile)
            self.assertIn(f'if (digits(0_k) /= {bits}) stop 77', profile)
            self.assertIn('if (reconstructed /= limit) error stop 3', profile)

    def test_each_literal_control_changes_only_one_source_line(self):
        self.assertEqual(len(self.controls), 20)
        for name, negative in self.negatives.items():
            control = self.controls[name.replace('_invalid__', '_valid__') + '_repair']
            before = (negative.root / 'source.f90').read_bytes().splitlines(keepends=True)
            after = (control.root / 'source.f90').read_bytes().splitlines(keepends=True)
            with self.subTest(case=name):
                self.assertEqual(len(before), len(after))
                self.assertEqual(sum(left != right for left, right in zip(before, after)), 1)
                self.assertEqual(negative.meta.profiles, control.meta.profiles)
                self.assertEqual(control.expectation.phase, 'compile')
                self.assertEqual(control.meta.evidence, 'positive-control')


if __name__ == '__main__':
    unittest.main()
