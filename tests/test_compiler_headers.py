import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run_tests as runner
from fixture_support import load_fixture
from suite_data import SuiteError, validate_compiler_header


class CompilerHeaderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.headers = self.root / 'processor/include'
        self.headers.mkdir(parents=True)
        self.bytes = b'#define CFI_VERSION 12345\n'
        self.header = self.headers / 'ISO_Fortran_binding.h'
        self.header.write_bytes(self.bytes)
        self.compiler = runner.Compiler('lfortran', 'lfortran', 'f23', version='fixed')

    def reply(self, directory):
        output = str(directory) + '\n'
        return runner.ProcessResult(0, output, stdout=output)

    def fixture(self, use_header=True):
        folder = self.root / 'fixture'
        folder.mkdir(exist_ok=True)
        (folder / 'main.f90').write_text('program p\nend program\n')
        (folder / 'checker.c').write_text('#include <ISO_Fortran_binding.h>\n')
        data = dict(
            schema_version=1, id='R601_valid__c_header', rule='R601', facets=[],
            files=['main.f90', 'checker.c'],
            build=[
                dict(id='main', source='main.f90', language='fortran', output='main.o'),
                dict(id='checker', source='checker.c', language='c', output='checker.o',
                     fortran_binding_header=use_header)],
            link=dict(objects=['main.o', 'checker.o'], output='program'),
            expect=dict(phase='run', outcome='success', exit_code=0))
        (folder / 'fixture.json').write_text(json.dumps(data))
        return load_fixture(folder / 'fixture.json', set())

    def test_advertised_header_is_hashed_and_cached(self):
        with patch.object(runner, 'run', return_value=self.reply(self.headers)) as run:
            first = runner.compiler_binding_header(self.compiler)
            second = runner.compiler_binding_header(self.compiler)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args[0][0], ['lfortran', '--print-c-include-dir'])
        self.assertIs(first, second)
        self.assertEqual(first['path'], str(self.header.resolve()))
        self.assertEqual(first['sha256'], hashlib.sha256(self.bytes).hexdigest())
        self.assertEqual(first['cfi_version'], '12345')

    def test_gnu_uses_its_own_include_query(self):
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        with patch.object(runner, 'run', return_value=self.reply(self.headers)) as run:
            result = runner.compiler_binding_header(comp)
        self.assertEqual(run.call_args[0][0], ['gfortran', '-print-file-name=include'])
        self.assertEqual(result['path'], str(self.header.resolve()))

    def test_flang_resource_query_locates_its_install_header(self):
        prefix = self.root / 'flang'
        resource = prefix / 'lib/clang/22'
        resource.mkdir(parents=True)
        header = prefix / 'include/flang/ISO_Fortran_binding.h'
        header.parent.mkdir(parents=True)
        header.write_bytes(self.bytes)
        comp = runner.Compiler('flang', 'flang', 'f2018')
        with patch.object(runner, 'run', return_value=self.reply(resource)):
            result = runner.compiler_binding_header(comp)
        self.assertEqual(result['path'], str(header.resolve()))
        other = resource / 'include/ISO_Fortran_binding.h'
        other.parent.mkdir(parents=True)
        other.write_bytes(b'#define CFI_VERSION 67890\n')
        comp.c_binding_header = {}
        with patch.object(runner, 'run', return_value=self.reply(resource)):
            with self.assertRaisesRegex(SuiteError, 'ambiguous'):
                runner.compiler_binding_header(comp)

    def test_missing_or_invalid_query_is_not_a_profile_skip(self):
        for response in (
            runner.ProcessResult(1, 'header query failed'),
            runner.ProcessResult(0, '', stdout=''),
            runner.ProcessResult(0, 'relative\n', stdout='relative\n'),
            runner.ProcessResult(0, '/one\n/two\n', stdout='/one\n/two\n'),
            runner.ProcessResult(0, str(self.root / 'missing') + '\n',
                                 stdout=str(self.root / 'missing') + '\n'),
            runner.ProcessResult(0, '', timed_out=True),
        ):
            with self.subTest(response=response):
                with patch.object(runner, 'run', return_value=response):
                    with self.assertRaises(SuiteError):
                        runner.compiler_binding_header(self.compiler)

    def test_only_the_processor_header_is_staged_for_the_c_step(self):
        (self.headers / 'stddef.h').write_text('not the companion standard header\n')
        fixture = self.fixture()
        commands = []

        def process(command, cwd, timeout, stdin=None):
            commands.append(command)
            if '--print-c-include-dir' in command:
                return self.reply(self.headers)
            if command[0] == 'cc':
                include = Path(command[command.index('-I') + 1])
                self.assertNotEqual(include, self.headers)
                self.assertEqual([path.name for path in include.iterdir()],
                                 ['ISO_Fortran_binding.h'])
                self.assertEqual((include / 'ISO_Fortran_binding.h').read_bytes(), self.bytes)
            if '-o' in command:
                Path(command[command.index('-o') + 1]).write_bytes(b'build artifact')
            return runner.ProcessResult(0, '')

        with patch.object(runner, 'run', side_effect=process):
            result = runner.check_fixture(fixture, self.compiler)
        self.assertEqual(result.outcome, 'pass')
        self.assertEqual([item['phase'] for item in result.trace],
                         ['compile', 'compile', 'link', 'run'])
        self.assertNotIn('-I', result.trace[0]['command'])
        self.assertNotIn('-I', result.trace[2]['command'])
        self.assertEqual(result.compiler_headers['ISO_Fortran_binding.h']['sha256'],
                         hashlib.sha256(self.bytes).hexdigest())
        self.assertEqual(result.input_hashes['@compiler/ISO_Fortran_binding.h'],
                         hashlib.sha256(self.bytes).hexdigest())
        self.assertEqual(self.header.read_bytes(), self.bytes)

    def test_version_mismatch_stays_a_runtime_failure(self):
        fixture = self.fixture()

        def process(command, cwd, timeout, stdin=None):
            if '--print-c-include-dir' in command:
                return self.reply(self.headers)
            if '-o' in command:
                Path(command[command.index('-o') + 1]).write_bytes(b'build artifact')
                return runner.ProcessResult(0, '')
            return runner.ProcessResult(1, 'descriptor version 1, expected 12345\n')

        with patch.object(runner, 'run', side_effect=process):
            result = runner.check_fixture(fixture, self.compiler)
        self.assertEqual(result.outcome, 'fail')
        self.assertEqual(result.phase, 'run')
        self.assertEqual(result.compiler_headers['ISO_Fortran_binding.h']['cfi_version'], '12345')

    def test_header_change_invalidates_cached_staging_and_snapshot(self):
        with patch.object(runner, 'run', return_value=self.reply(self.headers)):
            runner.compiler_binding_header(self.compiler)
        self.header.write_bytes(b'#define CFI_VERSION 54321\n')

        def process(command, cwd, timeout, stdin=None):
            if '-o' in command:
                Path(command[command.index('-o') + 1]).write_bytes(b'object')
            return runner.ProcessResult(0, '')

        with patch.object(runner, 'run', side_effect=process):
            with self.assertRaisesRegex(SuiteError, 'changed during the run'):
                runner.check_fixture(self.fixture(), self.compiler)
        same = runner.Compiler('lfortran', 'lfortran', 'f23', version='fixed')
        with patch.object(runner, 'Registry'), patch.object(runner, 'compiler', return_value=same):
            errors = runner.confirm_snapshot([self.compiler], [], {})
        self.assertTrue(any('binding header changed' in error for error in errors))

    def test_header_flag_cannot_shadow_processor_resources(self):
        fixture = self.fixture()
        data = json.loads(fixture.path.read_text())
        for mutate in (
            lambda: data['build'][0].update(fortran_binding_header=True),
            lambda: data['build'][1].update(fortran_binding_header='yes'),
        ):
            original = json.loads(json.dumps(data))
            mutate()
            fixture.path.write_text(json.dumps(data))
            with self.assertRaises(SuiteError):
                load_fixture(fixture.path, set())
            data = original
        (fixture.root / 'ISO_Fortran_binding.h').write_bytes(self.bytes)
        data['files'].append('ISO_Fortran_binding.h')
        fixture.path.write_text(json.dumps(data))
        with self.assertRaisesRegex(SuiteError, 'shadow'):
            load_fixture(fixture.path, set())

    def test_header_evidence_schema_requires_identity(self):
        valid = dict(path=str(self.header), sha256=hashlib.sha256(self.bytes).hexdigest(),
                     discovery='compiler-query')
        validate_compiler_header(valid, 'test')
        for update in ({'path': 'relative.h'}, {'sha256': 'bad'}, {'discovery': ''},
                       {'unknown': 'not allowed'}):
            with self.subTest(update=update):
                with self.assertRaises(SuiteError):
                    validate_compiler_header(dict(valid, **update), 'test')

    def test_reference_approval_requires_header_and_companion_provenance(self):
        fixture = self.fixture()
        case = runner.SuiteCase(fixture.name, fixture.rule, fixture.kind, str(fixture.path),
                                fixture.meta, fixture.name, fixture=fixture)
        registry = Mock()
        registry.requirements = {}
        registry.legacy = {}
        registry.fingerprint.return_value = 'a' * 64
        header = dict(path=str(self.header), sha256=hashlib.sha256(self.bytes).hexdigest(),
                      discovery='compiler-query')
        report = dict(
            run_errors=[],
            compilers=[dict(command='gfortran', version='GNU snapshot', standard='f2023',
                            c_binding_header=header)],
            c_compiler=dict(command='cc', version='C snapshot'),
            results=[dict(name=case.name, review=dict(fingerprint='a' * 64),
                          references={'gfortran': dict(
                              outcome='pass', phase='run',
                              compiler_headers={'ISO_Fortran_binding.h': header})})])
        path = self.root / 'report.json'
        path.write_text(json.dumps(report))
        runner.record_fixture_review(registry, [case], case.review_key, 'reference-validated',
                                     'Reviewed interface.', ['R601'], path)
        evidence = registry.record_review.call_args[0][-1][0]
        self.assertEqual(evidence['compiler_headers']['ISO_Fortran_binding.h'], header)
        self.assertEqual(evidence['c_compiler'], report['c_compiler'])
        for mutate in (
            lambda data: data['results'][0]['references']['gfortran'].pop('compiler_headers'),
            lambda data: data['compilers'][0]['c_binding_header'].update(sha256='b' * 64),
            lambda data: data.pop('c_compiler'),
        ):
            data = json.loads(json.dumps(report))
            mutate(data)
            path.write_text(json.dumps(data))
            with self.assertRaises(SuiteError):
                runner.record_fixture_review(registry, [case], case.review_key,
                                             'reference-validated', 'Reviewed.', ['R601'], path)


if __name__ == '__main__':
    unittest.main()
