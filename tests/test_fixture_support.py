import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fixture_support import load_fixture
import run_tests as runner
from suite_data import Review, SuiteError


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.raw = b'      program p\r\n      end\r\n'
        (self.root / 'source.f').write_bytes(self.raw)
        self.data = dict(
            schema_version=1, id='R601_valid__raw', rule='R601', facets=['source-form'],
            files=['source.f'],
            build=[dict(id='source', source='source.f', language='fortran', form='fixed', output='source.o')],
            link=dict(objects=['source.o'], output='program'),
            expect=dict(phase='run', outcome='success', exit_code=0, stdout='READY\n'))
        self.compiler = runner.Compiler('lfortran', 'lfortran', 'f23')
        self.exit_code = 0
        self.stdout = 'READY\n'
        self.stderr = ''
        self.commands = []

    def fixture(self):
        path = self.root / 'fixture.json'
        path.write_text(json.dumps(self.data))
        return load_fixture(path, set())

    def process(self, command, cwd, timeout, stdin=None):
        self.commands.append((command, cwd, stdin))
        if '-o' in command:
            output = Path(command[command.index('-o') + 1])
            output.write_bytes(b'object or executable')
            return runner.ProcessResult(0, '')
        return runner.ProcessResult(self.exit_code, self.stdout + self.stderr,
                                    stdout=self.stdout, stderr=self.stderr)

    def execute(self, fixture=None):
        with patch.object(runner, 'run', side_effect=self.process):
            return runner.check_fixture(fixture or self.fixture(), self.compiler)

    def test_raw_source_is_copied_byte_for_byte(self):
        def process(command, cwd, timeout, stdin=None):
            self.assertEqual((Path(cwd) / 'source.f').read_bytes(), self.raw)
            return self.process(command, cwd, timeout, stdin)
        with patch.object(runner, 'run', side_effect=process):
            result = runner.check_fixture(self.fixture(), self.compiler)
        self.assertEqual(result.outcome, 'pass')
        self.assertEqual(result.input_hashes['source.f'], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual((self.root / 'source.f').read_bytes(), self.raw)
        self.assertIn('--fixed-form', self.commands[0][0])
        self.assertEqual([step['phase'] for step in result.trace], ['compile', 'link', 'run'])

    def test_staging_normalization_is_rejected(self):
        def normalize(source, destination):
            Path(destination).write_text(Path(source).read_text())
        with patch.object(runner.shutil, 'copyfile', side_effect=normalize):
            with self.assertRaisesRegex(SuiteError, 'staging changed bytes'):
                self.execute()

    def test_declared_high_exit_status_is_not_a_compiler_crash(self):
        self.data['oracle_basis'] = 'processor-profile'
        self.data['oracle_profile'] = 'posix-stop-code'
        self.data['expect']['exit_code'] = 200
        self.exit_code = 200
        self.assertEqual(self.execute().outcome, 'pass')

    def test_high_compiler_exit_status_remains_a_failure(self):
        with patch.object(runner, 'run', return_value=runner.ProcessResult(200, '')):
            result = runner.check_fixture(self.fixture(), self.compiler)
        self.assertEqual(result.outcome, 'fail')
        self.assertEqual(result.phase, 'compile')

    def test_signal_is_not_prescribed_termination(self):
        self.data['oracle_basis'] = 'processor-profile'
        self.data['oracle_profile'] = 'posix-stop-code'
        self.data['expect']['exit_code'] = 200
        self.exit_code = -11
        self.assertEqual(self.execute().outcome, 'fail')

    def test_diagnostic_looking_runtime_data_is_not_a_compiler_error(self):
        self.stdout = 'Internal Compiler Error: ordinary application data\n'
        self.data['expect']['stdout'] = self.stdout
        self.assertEqual(self.execute().outcome, 'pass')

    def test_input_and_output_oracles_are_external(self):
        (self.root / 'input.txt').write_text('7\n')
        self.data['files'].append('input.txt')
        self.data['run'] = {'stdin_file': 'input.txt', 'arguments': ['argument']}
        self.data['expect']['files'] = {'result.txt': '49\n'}
        def process(command, cwd, timeout, stdin=None):
            if '-o' not in command:
                self.assertEqual(stdin, b'7\n')
                self.assertEqual(command[-1], 'argument')
                (Path(cwd) / 'result.txt').write_text('49\n')
            return self.process(command, cwd, timeout, stdin)
        with patch.object(runner, 'run', side_effect=process):
            result = runner.check_fixture(self.fixture(), self.compiler)
        self.assertEqual(result.outcome, 'pass')

    def test_exit_alone_cannot_hide_wrong_output(self):
        self.stdout = 'WRONG\n'
        self.assertEqual(self.execute().outcome, 'fail')

    def test_missing_output_file_fails(self):
        self.data['expect']['files'] = {'missing.txt': 'expected'}
        self.assertEqual(self.execute().outcome, 'fail')

    def test_binary_output_matches_an_immutable_fixture(self):
        (self.root / 'expected.bin').write_bytes(b'\x00\xff\x0d\x0a')
        self.data['files'].append('expected.bin')
        self.data['expect']['file_matches'] = {'result.bin': 'expected.bin'}
        def process(command, cwd, timeout, stdin=None):
            if '-o' not in command:
                (Path(cwd) / 'expected.bin').write_bytes(b'changed staged input')
                (Path(cwd) / 'result.bin').write_bytes(b'\x00\xff\x0d\x0a')
            return self.process(command, cwd, timeout, stdin)
        with patch.object(runner, 'run', side_effect=process):
            result = runner.check_fixture(self.fixture(), self.compiler)
        self.assertEqual(result.outcome, 'pass')

    def test_non_utf8_output_cannot_match_a_text_escape(self):
        self.data['expect']['stdout'] = r'\xff'
        def process(command, cwd, timeout, stdin=None):
            result = self.process(command, cwd, timeout, stdin)
            if '-o' not in command:
                result.stdout = r'\xff'
                result.stdout_bytes = b'\xff'
            return result
        with patch.object(runner, 'run', side_effect=process):
            result = runner.check_fixture(self.fixture(), self.compiler)
        self.assertEqual(result.outcome, 'fail')

    def test_undeclared_asset_is_not_silently_ignored(self):
        (self.root / 'forgotten.h').write_text('int f(void);\n')
        with self.assertRaisesRegex(SuiteError, 'undeclared fixture'):
            self.fixture()

    def test_allowed_output_alternatives(self):
        self.data['expect']['stdout'] = ['FIRST\n', 'SECOND\n']
        self.stdout = 'SECOND\n'
        self.assertEqual(self.execute().outcome, 'pass')

    def test_earlier_compile_error_cannot_satisfy_link_rejection(self):
        self.data['expect'] = dict(phase='link', outcome='reject',
                                   diagnostic=dict(contains_any=['duplicate symbol']))
        with patch.object(runner, 'run', return_value=runner.ProcessResult(1, 'error: duplicate symbol')):
            result = runner.check_fixture(self.fixture(), self.compiler)
        self.assertEqual(result.outcome, 'fail')
        self.assertEqual(result.phase, 'compile')

    def test_eof_rejection_does_not_add_a_marker_or_newline(self):
        raw = b'program p\nimplicit none'
        (self.root / 'source.f').write_bytes(raw)
        self.data.pop('link')
        self.data['expect'] = dict(phase='compile', step='source', outcome='reject',
                                   diagnostic=dict(file='source.f', anchor='eof',
                                                   contains_any=['unexpected end of file']))
        def process(command, cwd, timeout, stdin=None):
            self.assertEqual((Path(cwd) / 'source.f').read_bytes(), raw)
            return runner.ProcessResult(1, "Error: Unexpected end of file in 'source.f'")
        with patch.object(runner, 'run', side_effect=process):
            result = runner.check_fixture(self.fixture(), self.compiler)
        self.assertEqual(result.outcome, 'pass')

    def test_runtime_negative_is_not_generic_any_failure(self):
        self.data['expect']['outcome'] = 'reject'
        with self.assertRaises(SuiteError):
            self.fixture()

    def test_nonzero_status_requires_profile_or_policy(self):
        self.data['expect']['exit_code'] = 200
        with self.assertRaises(SuiteError):
            self.fixture()

    def test_undeclared_files_and_outputs_are_rejected(self):
        for mutate in (
            lambda: self.data['build'][0].update(source='../outside.f90'),
            lambda: self.data['build'][0].update(output='source.f'),
            lambda: self.data['link'].update(objects=['unknown.o']),
            lambda: self.data['build'][0].update(depends_on=['later']),
        ):
            old = json.loads(json.dumps(self.data))
            mutate()
            with self.assertRaises(SuiteError):
                self.fixture()
            self.data = old

    def test_unapproved_or_stale_fixture_cannot_be_baselined(self):
        path = self.root / 'xfail.txt'
        original = 'existing # keep\n'
        for state in ('unreviewed', 'disputed', 'needs-oracle', 'stale'):
            path.write_text(original)
            result = dict(name='new', check=runner.Check('fail', 'reason'), review=Review(state))
            with self.assertRaises(SuiteError):
                runner.update_xfail(str(path), [result])
            self.assertEqual(path.read_text(), original)
            self.assertNotEqual(runner.status('new', runner.Check('pass'), {'new'}, Review(state)), 'XPASS')

    def test_c_build_and_fortran_link_are_distinct_steps(self):
        (self.root / 'bridge.c').write_text('int f(void) { return 7; }\n')
        self.data['files'].append('bridge.c')
        self.data['build'].append(dict(id='c', source='bridge.c', language='c', output='bridge.o',
                                       depends_on=['source']))
        self.data['link']['objects'].append('bridge.o')
        result = self.execute()
        self.assertEqual(result.outcome, 'pass')
        self.assertEqual(self.commands[1][0][0], 'cc')
        self.assertIn('-std=c11', self.commands[1][0])
        self.assertEqual(self.commands[2][0][0], 'lfortran')


if __name__ == '__main__':
    unittest.main()
