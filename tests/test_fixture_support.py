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

    def reporting_fixture(self):
        self.data.pop('link', None)
        self.data['id'] = 'R601_invalid__reports'
        self.data['expect'] = dict(
            phase='compile', step='source', outcome='diagnose',
            diagnostic=dict(file='source.f', line=2, allow_nonfatal=[
                dict(compiler='flang', severity='portability', contains_any=['missing space'])]))
        return self.fixture()

    def driver_reporting_fixture(self):
        self.reporting_fixture()
        self.data['build'][0]['form'] = 'free'
        self.data['expect']['diagnostic']['allow_nonfatal'] = [
            dict(compiler='gfortran', severity='warning',
                 equals_any=["'&' not allowed by itself"], attribution='single-source-driver')]
        return self.fixture()

    def test_declared_statement_span_accepts_only_contained_diagnostics(self):
        self.reporting_fixture()
        self.data['expect']['diagnostic'].update(line=1, end_line=2)
        fixture = self.fixture()
        for first, last, expected in ((1, 1, 'pass'), (2, 2, 'pass'), (1, 2, 'pass'),
                                      (1, 3, 'fail'), (3, 3, 'fail'), (2, 1, 'fail'),
                                      (0, 2, 'fail'), (1, 1000000000, 'fail')):
            with self.subTest(first=first, last=last):
                output = f'source.f:{first}-{last}:1-20: syntax error: malformed statement\n'
                with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
                    result = runner.check_fixture(fixture, self.compiler)
                self.assertEqual(result.outcome, expected)
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        for line, expected in ((1, 'pass'), (2, 'pass'), (3, 'fail')):
            with self.subTest(reference_line=line):
                output = f'source.f:{line}:1: Error: Unclassifiable statement\n'
                with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
                    result = runner.check_fixture(fixture, comp)
                self.assertEqual(result.outcome, expected)

    def test_statement_span_schema_rejects_invalid_bounds(self):
        self.reporting_fixture()
        for end_line in (1, True, None, '3'):
            with self.subTest(end_line=end_line):
                self.data['expect']['diagnostic']['end_line'] = end_line
                with self.assertRaises(SuiteError):
                    self.fixture()

    def test_eof_position_is_explicit_and_not_an_unlocated_summary(self):
        self.reporting_fixture()
        self.data['expect']['diagnostic'].update(
            line=2, end_line=3, contains_any=['end of file', "bad character ('&')"])
        fixture = self.fixture()
        for output, expected in (
            ('source.f:3-3:1-1: syntax error: End of file is unexpected here\n', 'pass'),
            ('source.f:1-3:1-1: syntax error: End of file is unexpected here\n', 'fail'),
            ('error: Could not scan source.f\n', 'fail'),
            ('error: End of file in source.f\n', 'fail'),
            ('other.f:3-3:1-1: syntax error: End of file is unexpected here\n', 'fail'),
            ('source.f:3-3:1-1: syntax error: Cannot open output\n! end of file\n', 'fail'),
        ):
            with self.subTest(output=output):
                with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
                    result = runner.check_fixture(fixture, self.compiler)
                self.assertEqual(result.outcome, expected)

    def test_exact_driver_warning_can_be_bound_to_the_only_source(self):
        fixture = self.driver_reporting_fixture()
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        output = "f951: Warning: '&' not allowed by itself in line 2\n"
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
            result = runner.check_fixture(fixture, comp)
        self.assertEqual(result.outcome, 'pass')
        self.assertIn('single-source driver attribution', result.note)
        self.assertEqual(runner.reference_label(result, 'invalid'), 'diagnoses')
        self.assertEqual(result.trace[0]['returncode'], 0)
        self.assertTrue(result.input_hashes)
        self.assertEqual(result.output, output)

    def test_driver_attribution_rejects_ambiguous_or_unrelated_output(self):
        fixture = self.driver_reporting_fixture()
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        wanted = "f951: Warning: '&' not allowed by itself in line 2\n"
        for output in (
            wanted.replace('line 2', 'line 1'),
            wanted.replace('Warning:', 'Error:'),
            wanted.replace('f951:', 'another-driver:'),
            wanted.replace("'&' not allowed by itself", "unrelated warning"),
            wanted.replace("'&' not allowed by itself", "other.f: '&' not allowed by itself"),
            wanted.replace(' in line 2', ''),
            'other.f:2:1: warning: unrelated\n' + wanted,
            '/another/directory/source.f:2:1: in the context: statement\n' + wanted,
            'f951: Warning: Inconsistent internal state: No location in statement\n',
        ):
            with self.subTest(output=output):
                with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
                    result = runner.check_fixture(fixture, comp)
                self.assertEqual(result.outcome, 'fail')

    def test_driver_attribution_requires_its_explicit_qualified_context(self):
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        output = "f951: Warning: '&' not allowed by itself in line 2\n"
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
            result = runner.check_fixture(self.reporting_fixture(), comp)
        self.assertEqual(result.outcome, 'fail')
        with self.assertRaises(SuiteError):
            runner.driver_warning_diagnostics(output, 'source.f', None)
        self.driver_reporting_fixture()
        self.data['build'][0]['form'] = 'fixed'
        with self.assertRaises(SuiteError):
            self.fixture()
        self.data['build'][0]['form'] = 'free'
        for raw in (b"include 'other.inc'\n", b"program p\n!\xff\nend\n"):
            (self.root / 'source.f').write_bytes(raw)
            with self.subTest(raw=raw):
                with self.assertRaises(SuiteError):
                    self.fixture()
        (self.root / 'source.f').write_bytes(self.raw)
        (self.root / 'other.f').write_bytes(self.raw)
        self.data['files'].append('other.f')
        with self.assertRaises(SuiteError):
            self.fixture()

    def test_driver_predicate_schema_requires_exact_gnu_warning(self):
        self.driver_reporting_fixture()
        original = json.loads(json.dumps(self.data))
        for update in (
            {'compiler': 'flang'}, {'severity': 'portability'}, {'attribution': 'guess'},
            {'contains_any': ['allowed']}, {'equals_any': []},
        ):
            with self.subTest(update=update):
                self.data = json.loads(json.dumps(original))
                self.data['expect']['diagnostic']['allow_nonfatal'][0].update(update)
                with self.assertRaises(SuiteError):
                    self.fixture()
        self.data = json.loads(json.dumps(original))
        predicate = self.data['expect']['diagnostic']['allow_nonfatal'][0]
        predicate['contains_any'] = predicate.pop('equals_any')
        with self.assertRaises(SuiteError):
            self.fixture()

    def test_driver_or_eof_diagnostic_cannot_hide_a_compiler_failure(self):
        fixture = self.driver_reporting_fixture()
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        wanted = "f951: Warning: '&' not allowed by itself in line 2\n"
        for process in (
            runner.ProcessResult(1, wanted + 'internal compiler error: Segmentation fault: 11\n'),
            runner.ProcessResult(1, wanted + 'f951: Fatal Error: Out of memory\n'),
            runner.ProcessResult(1, wanted + 'gfortran: fatal error: Killed signal terminated program f951\n'),
            runner.ProcessResult(-11, wanted),
            runner.ProcessResult(0, wanted, timed_out=True),
        ):
            with self.subTest(process=process):
                with patch.object(runner, 'run', return_value=process):
                    result = runner.check_fixture(fixture, comp)
                self.assertEqual(result.outcome, 'fail')

    def test_reporting_fixture_is_invalid_input_without_requiring_rejection(self):
        fixture = self.reporting_fixture()
        comp = runner.Compiler('flang', 'flang', 'f2018')
        output = 'source.f:2:7: portability: missing space\n'
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
            result = runner.check_fixture(fixture, comp)
        self.assertEqual(fixture.kind, 'invalid')
        self.assertEqual(result.outcome, 'pass')
        self.assertEqual(result.note, 'diagnoses without rejection')
        self.assertEqual(runner.reference_label(result, fixture.kind), 'diagnoses')
        self.assertEqual([entry['phase'] for entry in result.trace], ['compile'])
        self.assertEqual(result.input_hashes['source.f'], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual((self.root / 'source.f').read_bytes(), self.raw)

    def test_reporting_requires_matching_file_line_severity_and_message(self):
        fixture = self.reporting_fixture()
        comp = runner.Compiler('flang', 'flang', 'f2018')
        for output in (
            'other.f:2:7: portability: missing space\n',
            'source.f:1:7: portability: missing space\n',
            'source.f:2:7: warning: missing space\n',
            'source.f:2:7: portability: unused variable\n',
            'portability: missing space\n',
            'source.f:2:7: portability: unused variable\n  ! missing space\n',
            'source.f:2:7: in the context: statement\nerror: driver failed\n',
        ):
            with self.subTest(output=output):
                with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
                    result = runner.check_fixture(fixture, comp)
                self.assertEqual(result.outcome, 'fail')

    def test_reporting_nonfatal_allowance_is_compiler_specific(self):
        fixture = self.reporting_fixture()
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        output = 'source.f:2:7: portability: missing space\n'
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
            result = runner.check_fixture(fixture, comp)
        self.assertEqual(result.outcome, 'fail')

    def test_reporting_errors_are_independent_of_ordinary_exit_status(self):
        fixture = self.reporting_fixture()
        for code in (0, 1):
            for comp, output in (
                (self.compiler, 'source.f:1-3:1-20: syntax error [R601]: invalid token\n'),
                (runner.Compiler('gfortran', 'gfortran', 'f2023'),
                 'source.f:2:7:\n    2 | invalid\nError: invalid token\n'),
            ):
                with self.subTest(code=code, compiler=comp.family):
                    with patch.object(runner, 'run', return_value=runner.ProcessResult(code, output)):
                        result = runner.check_fixture(fixture, comp)
                    self.assertEqual(result.outcome, 'pass')

    def test_reporting_preserves_codes_mode(self):
        fixture = self.reporting_fixture()
        for tag, expected in (('[R601]', 'pass'), ('[R602]', 'fail'), ('', 'fail')):
            output = f'source.f:2-2:1-20: syntax error {tag}: invalid token\n'
            output = output.replace('error :', 'error:')
            with self.subTest(tag=tag):
                with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
                    result = runner.check_fixture(fixture, self.compiler, codes=True)
                self.assertEqual(result.outcome, expected)

    def test_reporting_lfortran_warnings_require_explicit_allowance(self):
        self.reporting_fixture()
        output = 'source.f:2-2:1-20: semantic warning [R601]: missing space\n'
        for allowed, expected in (([], 'fail'), (
                [dict(compiler='lfortran', severity='warning', contains_any=['missing space'])], 'pass')):
            self.data['expect']['diagnostic']['allow_nonfatal'] = allowed
            with self.subTest(allowed=allowed):
                with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
                    result = runner.check_fixture(self.fixture(), self.compiler)
                self.assertEqual(result.outcome, expected)
        self.assertEqual(runner.lfortran_errors(output), [])

    def test_reporting_predicate_does_not_match_source_echo_or_another_diagnostic(self):
        self.reporting_fixture()
        self.data['expect']['diagnostic']['contains_any'] = ['missing space']
        for output in (
            'source.f:2-2:1-20: syntax error: unrelated\n! missing space\n',
            'source.f:1-1:1-20: syntax error: missing space\n'
            'source.f:2-2:1-20: syntax error: unrelated\n',
        ):
            with self.subTest(output=output):
                with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
                    result = runner.check_fixture(self.fixture(), self.compiler)
                self.assertEqual(result.outcome, 'fail')

    def test_reporting_crashes_verifier_failures_and_timeouts_never_pass(self):
        fixture = self.reporting_fixture()
        output = 'source.f:2-2:1-20: syntax error [R601]: invalid token\n'
        for process in (
            runner.ProcessResult(-11, output),
            runner.ProcessResult(139, output),
            runner.ProcessResult(1, output + 'LLVM ERROR: aborting'),
            runner.ProcessResult(1, output + 'ASR verify pass error: invalid IR'),
            runner.ProcessResult(0, output, timed_out=True),
        ):
            with self.subTest(process=process):
                with patch.object(runner, 'run', return_value=process):
                    result = runner.check_fixture(fixture, self.compiler)
                self.assertEqual(result.outcome, 'fail')

    def test_earlier_failure_cannot_satisfy_later_reporting_step(self):
        self.reporting_fixture()
        self.data['build'].insert(0, dict(
            id='earlier', source='source.f', language='fortran', form='fixed', output='earlier.o'))
        self.data['build'][1]['depends_on'] = ['earlier']
        output = 'source.f:2-2:1-20: syntax error [R601]: invalid token\n'
        with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
            result = runner.check_fixture(self.fixture(), self.compiler)
        self.assertEqual(result.outcome, 'fail')
        self.assertEqual([entry['step'] for entry in result.trace], ['earlier'])

    def test_reporting_schema_requires_precise_compile_contract(self):
        self.reporting_fixture()
        original = json.loads(json.dumps(self.data))
        mutations = (
            lambda: self.data['expect'].update(phase='link'),
            lambda: self.data['expect'].update(phase='run'),
            lambda: self.data['expect'].update(step='missing'),
            lambda: self.data['expect']['diagnostic'].pop('file'),
            lambda: self.data['expect']['diagnostic'].pop('line'),
            lambda: self.data['expect']['diagnostic'].update(line=0),
            lambda: self.data['expect']['diagnostic'].update(line=True),
            lambda: self.data['expect']['diagnostic'].update(file={}),
            lambda: self.data['expect']['diagnostic'].update(file='source.o'),
            lambda: self.data['expect']['diagnostic'].update(anchor='file'),
            lambda: self.data['expect']['diagnostic'].update(allow_nonfatal={}),
            lambda: self.data['expect']['diagnostic']['allow_nonfatal'][0].update(compiler='unknown'),
            lambda: self.data['expect']['diagnostic']['allow_nonfatal'][0].update(compiler={}),
            lambda: self.data['expect']['diagnostic']['allow_nonfatal'][0].update(severity='error'),
            lambda: self.data['expect']['diagnostic']['allow_nonfatal'][0].update(contains_any=[]),
            lambda: self.data['expect']['diagnostic']['allow_nonfatal'][0].update(contains_any=[' ']),
            lambda: self.data['expect']['diagnostic']['allow_nonfatal'][0].update(extra='ignored'),
        )
        for index, mutate in enumerate(mutations):
            self.data = json.loads(json.dumps(original))
            with self.subTest(index=index):
                mutate()
                with self.assertRaises(SuiteError):
                    self.fixture()

    def test_reporting_opt_in_does_not_relax_manifest_rejection(self):
        self.reporting_fixture()
        self.data['expect']['outcome'] = 'reject'
        with self.assertRaises(SuiteError):
            self.fixture()
        self.data['expect']['diagnostic'].pop('allow_nonfatal')
        output = 'source.f:2-2:1-20: syntax error [R601]: invalid token\n'
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
            result = runner.check_fixture(self.fixture(), self.compiler)
        self.assertEqual(result.outcome, 'fail')

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

    def test_located_manifest_rejection_requests_short_diagnostics(self):
        self.data.pop('link')
        self.data['expect'] = dict(
            phase='compile', step='source', outcome='reject',
            diagnostic=dict(file='source.f', line=2))

        def process(command, cwd, timeout, stdin=None):
            index = command.index('--error-format')
            self.assertEqual(command[index + 1], 'short')
            source = Path(cwd) / 'source.f'
            return runner.ProcessResult(1, f'{source}:2-2:7-12: syntax error: Invalid source form\n')

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
