import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

import run_tests as runner
from execution_commands import case_plan
from suite_data import Registry, SuiteError, write_json


class CaseContractTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.tests = self.root / 'tests'
        self.tests.mkdir()
        standard = dict(document='synthetic', edition='F2023', sha256='a' * 64)
        write_json(self.root / 'source.json', dict(standard, sections={
            '1.1': dict(units={'C601': dict(kind='numbered-item', sha256='b' * 64)})}))
        (self.root / 'rules.txt').write_text('C601 synthetic constraint\n')
        write_json(self.root / 'catalogue.json', dict(
            schema_version=1, section='1.1', requirements=[
                dict(id='C601', title='Synthetic', source='C601', source_units=['C601'],
                     category='restriction', diagnostic_obligation='required',
                     definition='Two separately attributed contexts.', facets=['one', 'two'],
                     pending={}, oracle='A located synthetic report.')],
            accounting=[dict(unit='C601', disposition='requirements', requirements=['C601'])]))
        write_json(self.root / 'index.json', dict(
            schema_version=1, standard=standard, source_inventory='source.json',
            rule_inventory='rules.txt', catalogues=['catalogue.json'], reviews='reviews.json'))
        self.source = self.tests / 'C601_invalid.f90'
        self.original = (
            '! case: first\nprogram first\ninteger :: x, x ! {error C601 first}\nend program\n'
            '! case: second\nprogram second\nreal :: y, y ! {error C601 second}\nend program\n')
        self.source.write_text(self.original)
        self.path = self.tests / 'C601_invalid.cases.json'
        self.data = dict(schema_version=1, cases={
            name: dict(facets=[facet], outcome='diagnose',
                       diagnostic=dict(contains_any=['synthetic problem'], excludes_any=['not implemented']))
            for name, facet in [('first', 'one'), ('second', 'two')]})
        write_json(self.path, self.data)

    def registry(self):
        return Registry(self.root, 'index.json')

    def cases(self, registry=None):
        return runner.collect_cases(self.tests, registry or self.registry())

    def test_retained_path_ids_and_source_bytes_have_per_execution_metadata(self):
        registry = self.registry()
        cases = self.cases(registry)
        self.assertEqual([case.name for case in cases], ['C601_invalid:first', 'C601_invalid:second'])
        self.assertEqual([case.review_key for case in cases], [case.name for case in cases])
        self.assertEqual([case.meta.facets for case in cases], [['one'], ['two']])
        self.assertEqual({case.path for case in cases}, {str(self.source)})
        self.assertEqual(self.source.read_text(), self.original)
        self.assertEqual([case.contract['diagnostic']['line'] for case in cases], [3, 7])
        self.assertNotEqual(cases[0].fingerprint(registry), cases[1].fingerprint(registry))
        self.assertEqual(case_plan(cases[0])['expectation']['outcome'], 'diagnose')

    def test_missing_unknown_incomplete_and_malformed_contracts_fail(self):
        for modify in (
                lambda data: data['cases'].pop('second'),
                lambda data: data['cases'].update(extra=data['cases']['first']),
                lambda data: data['cases']['first'].update(profiles=['no-such-profile']),
                lambda data: data['cases']['first'].update(outcome='success'),
                lambda data: data['cases']['first']['diagnostic'].update(line=4),
                lambda data: data['cases']['first']['diagnostic'].update(line=2, end_line=2),
                lambda data: data['cases']['first']['diagnostic'].update(file='other.f90'),
                lambda data: data['cases']['first']['diagnostic'].update(contains_any=[])):
            data = copy.deepcopy(self.data)
            modify(data)
            write_json(self.path, data)
            with self.subTest(modify=modify), self.assertRaises(SuiteError):
                self.cases()

    def test_orphan_sidecar_is_not_silently_ignored(self):
        self.source.unlink()
        with self.assertRaisesRegex(SuiteError, 'no retained invalid source'):
            self.cases()

    def test_contract_change_invalidates_the_corresponding_review(self):
        registry = self.registry()
        before = {case.name: case.fingerprint(registry) for case in self.cases(registry)}
        self.data['cases']['first']['diagnostic']['contains_any'] = ['changed cause']
        write_json(self.path, self.data)
        after = {case.name: case.fingerprint(registry) for case in self.cases(registry)}
        self.assertNotEqual(before['C601_invalid:first'], after['C601_invalid:first'])
        self.assertEqual(before['C601_invalid:second'], after['C601_invalid:second'])

    def test_selected_snapshot_rereads_effective_contract_without_an_aggregate(self):
        registry = self.registry()
        cases = self.cases(registry)
        first = cases[0]
        fingerprints = {case.review_key: case.fingerprint(registry) for case in cases}
        self.data['cases']['second']['diagnostic']['contains_any'] = ['changed unrelated cause']
        write_json(self.path, self.data)
        with patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'Registry', side_effect=self.registry):
            self.assertEqual(runner.confirm_snapshot([], [first], fingerprints), [])
            self.data['cases']['first']['diagnostic']['contains_any'] = ['changed selected cause']
            write_json(self.path, self.data)
            errors = runner.confirm_snapshot([], [first], fingerprints,
                                             evidence_snapshot={}, execution_snapshot={})
        self.assertTrue(any('inputs or requirement changed' in error for error in errors))

    def test_mid_run_sidecar_change_is_provisional_and_cannot_update_baseline(self):
        registry = self.registry()
        cases = self.cases(registry)
        for case in cases:
            runner.record_fixture_review(registry, cases, case.review_key, 'source-reviewed',
                                         'Synthetic original contract reviewed.', [])
        report = self.root / 'changed-contract.json'

        def compiler(command, target, standard, launcher, timeout):
            return runner.Compiler(command, 'lfortran', 'f23', version='fixed', launcher=launcher)

        def transport(command, cwd, timeout=30, stdin=None):
            self.data['cases']['first']['diagnostic']['contains_any'] = ['new exact diagnostic cause']
            write_json(self.path, self.data)
            return runner.ProcessResult(
                0, f'{command[-1]}:3-3:1-12: semantic error: synthetic problem')

        with patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'Registry', side_effect=self.registry), \
                patch.object(runner, 'compiler', side_effect=compiler), \
                patch.object(runner, 'run', side_effect=transport), \
                patch.object(runner, 'update_xfail') as update, \
                patch.object(sys, 'argv', [
                    'run_tests.py', '-t', 'C601_invalid:first', '--update-xfail', '--report', str(report)]), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            status = runner.main()
        self.assertEqual(status, 2)
        update.assert_not_called()
        data = json.loads(report.read_text())
        self.assertTrue(data['run_errors'])
        self.assertEqual(data['results'][0]['check']['outcome'], 'pass')
        self.assertEqual(self.source.read_text(), self.original)

    def test_exact_marker_or_declared_relation_and_causal_diagnose_are_used(self):
        self.data['cases']['first']['diagnostic'].update(line=2, end_line=3)
        write_json(self.path, self.data)
        first = self.cases()[0]
        compiler = runner.Compiler('lfortran', 'lfortran', 'f23')
        for line, message, expected in (
                (2, 'synthetic problem', 'pass'),
                (3, 'synthetic problem', 'pass'),
                (1, 'synthetic problem', 'fail'),
                (3, 'not implemented: synthetic problem', 'fail')):
            output = f'C601_invalid.f90:{line}-{line}:1-8: semantic error: {message}'
            with self.subTest(line=line, message=message), patch.object(
                    runner, 'run', return_value=runner.ProcessResult(0, output)):
                result = runner.execute_case(first, compiler)
            self.assertEqual(result.outcome, expected)
            self.assertEqual(result.phase, 'compile')
            self.assertEqual(result.trace[0]['returncode'], 0)
            self.assertIn('C601_invalid.f90', result.input_hashes)

    def test_exact_selector_is_shared_and_retains_sidecar_marker_and_filename_rules(self):
        first = self.data['cases']['first']['diagnostic']
        first['equals_any'] = first.pop('contains_any')
        write_json(self.path, self.data)
        cases = self.cases()
        self.assertEqual(cases[0].contract['diagnostic']['file'], self.source.name)
        self.assertEqual(cases[0].contract['diagnostic']['line'], 3)
        self.assertEqual(cases[0].contract['diagnostic']['equals_any'], ['synthetic problem'])
        original = copy.deepcopy(self.data)
        for change in (
                {'equals_any': []}, {'equals_any': ['']}, {'equals_any': [' ']},
                {'equals_any': None}, {'equals_any': ['cause', 'CAUSE']},
                {'contains_any': ['cause']}, {'file': 'other.f90'},
                {'line': 4}, {'line': 1, 'end_line': 2}):
            candidate = copy.deepcopy(original)
            candidate['cases']['first']['diagnostic'].update(change)
            write_json(self.path, candidate)
            with self.subTest(change=change), self.assertRaises(SuiteError):
                self.cases()

    def test_exact_retained_diagnose_uses_actual_staging_not_a_foreign_basename(self):
        diagnostic = self.data['cases']['first']['diagnostic']
        diagnostic['equals_any'] = diagnostic.pop('contains_any')
        write_json(self.path, self.data)
        case = self.cases()[0]
        for family, mode in (('lfortran', 'f23'), ('gfortran', 'f2023'), ('flang', 'f2018')):
            comp = runner.Compiler(family, family, mode)
            for status in (0, 1, 2):
                for codes in (False, True):
                    for foreign in (False, True):
                        for message in ('synthetic problem', 'Quoted diagnostic: "synthetic problem"'):
                            def transport(command, cwd, timeout=30, stdin=None):
                                staged = Path(command[-1])
                                self.assertEqual(staged.name, self.source.name)
                                self.assertEqual(staged.read_text(), case.isolated[-1])
                                self.assertIn('! {error C601 first}', staged.read_text())
                                location = '/foreign/' + staged.name if foreign else str(staged)
                                text = (f'{location}:3-3:1-40: semantic error [C601]: {message}'
                                        if family == 'lfortran' else f'{location}:3:1: error: {message}')
                                return runner.ProcessResult(status, text)

                            with self.subTest(family=family, status=status, codes=codes,
                                              foreign=foreign, message=message), patch.object(
                                    runner, 'run', side_effect=transport):
                                result = runner.execute_case(case, comp, codes=codes)
                            self.assertEqual(result.outcome,
                                             'pass' if not foreign and message == 'synthetic problem' else 'fail')
                            self.assertEqual((len(result.trace), result.phase), (1, 'compile'))
        self.assertEqual(self.source.read_text(), self.original)

    def test_exact_selector_changes_only_its_sidecar_fingerprint_and_snapshot(self):
        registry = self.registry()
        before_cases = self.cases(registry)
        before = {case.name: case.fingerprint(registry) for case in before_cases}
        diagnostic = self.data['cases']['first']['diagnostic']
        diagnostic['equals_any'] = diagnostic.pop('contains_any')
        write_json(self.path, self.data)
        after = {case.name: case.fingerprint(registry) for case in self.cases(registry)}
        self.assertNotEqual(before[before_cases[0].name], after[before_cases[0].name])
        self.assertEqual(before[before_cases[1].name], after[before_cases[1].name])
        with patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'Registry', side_effect=self.registry):
            errors = runner.confirm_snapshot([], [before_cases[0]], before)
        self.assertTrue(any('inputs or requirement changed' in error for error in errors))

    def test_mid_run_manifest_selector_or_source_origin_change_prevents_baseline_update(self):
        directory = self.tests / 'fixtures/precision'
        directory.mkdir(parents=True)
        (directory / 'source.f90').write_text('synthetic primary\n')
        (directory / 'included').write_text('synthetic included\n')
        manifest = directory / 'fixture.json'
        baseline = self.tests / 'expected_failures.txt'
        baseline.write_text('# synthetic unchanged baseline\n')
        for mutation in ('selector', 'origin'):
            data = dict(
                schema_version=1, id='C601_invalid__precision', rule='C601', facets=['one'],
                files=['source.f90', 'included'],
                build=[dict(id='source', source='source.f90', language='fortran', output='source.o')],
                expect=dict(phase='compile', step='source', outcome='diagnose',
                            diagnostic=dict(file='source.f90', line=1, contains_any=['actual cause'])))
            write_json(manifest, data)
            registry = self.registry()
            cases = self.cases(registry)
            selected = next(case for case in cases if case.name == data['id'])
            runner.record_fixture_review(registry, cases, selected.review_key, 'source-reviewed',
                                         'Synthetic original fixture contract, not a real approval.', [])
            report = self.root / (mutation + '-snapshot.json')

            def compiler(command, target, standard, launcher, timeout):
                return runner.Compiler(command, 'lfortran', 'f23', version='fixed', launcher=launcher)

            def transport(command, cwd, timeout=30, stdin=None):
                source = command[command.index('-c') + 1]
                diagnostic = data['expect']['diagnostic']
                if mutation == 'selector':
                    diagnostic['equals_any'] = diagnostic.pop('contains_any')
                else:
                    diagnostic['file'] = 'included'
                write_json(manifest, data)
                return runner.ProcessResult(0, f'{source}:1-1:1-20: semantic error: actual cause')

            with self.subTest(mutation=mutation), patch.object(runner, 'HERE', str(self.tests)), \
                    patch.object(runner, 'Registry', side_effect=self.registry), \
                    patch.object(runner, 'compiler', side_effect=compiler), \
                    patch.object(runner, 'run', side_effect=transport), \
                    patch.object(runner, 'update_xfail') as update, \
                    patch.object(sys, 'argv', ['run_tests.py', '-t', data['id'],
                                              '--update-xfail', '--report', str(report)]), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                status = runner.main()
            self.assertEqual(status, 2)
            update.assert_not_called()
            recorded = json.loads(report.read_text())
            self.assertEqual(recorded['results'][0]['check']['outcome'], 'pass')
            self.assertTrue(recorded['run_errors'])
            self.assertEqual(baseline.read_text(), '# synthetic unchanged baseline\n')

    def test_mid_run_exact_sidecar_selector_cannot_write_baseline(self):
        registry = self.registry()
        cases = self.cases(registry)
        for case in cases:
            runner.record_fixture_review(registry, cases, case.review_key, 'source-reviewed',
                                         'Synthetic sidecar snapshot, not a real approval.', [])
        report = self.root / 'exact-sidecar-change.json'

        def compiler(command, target, standard, launcher, timeout):
            return runner.Compiler(command, 'lfortran', 'f23', version='fixed', launcher=launcher)

        def transport(command, cwd, timeout=30, stdin=None):
            diagnostic = self.data['cases']['first']['diagnostic']
            diagnostic['equals_any'] = diagnostic.pop('contains_any')
            write_json(self.path, self.data)
            return runner.ProcessResult(0, f'{command[-1]}:3-3:1-30: semantic error: synthetic problem')

        with patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'Registry', side_effect=self.registry), \
                patch.object(runner, 'compiler', side_effect=compiler), \
                patch.object(runner, 'run', side_effect=transport), \
                patch.object(runner, 'update_xfail') as update, \
                patch.object(sys, 'argv', ['run_tests.py', '-t', 'C601_invalid:first',
                                          '--update-xfail', '--report', str(report)]), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(runner.main(), 2)
        update.assert_not_called()
        self.assertTrue(json.loads(report.read_text())['run_errors'])


if __name__ == '__main__':
    unittest.main()
