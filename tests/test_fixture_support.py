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

    def test_driver_attribution_rejects_malformed_competitive_locations(self):
        fixture = self.driver_reporting_fixture()
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        wanted = "f951: Warning: '&' not allowed by itself in line 2\n"
        for origin in ('source.f', 'other.f90', 'other.inc'):
            for columns in ('5-', '5--8', '5-x', '5-8-9', '8-5', '0-8'):
                for status in (0, 1):
                    with self.subTest(origin=origin, columns=columns, status=status):
                        output = f'source.f:2:1:\n{origin}:9:{columns}:\n' + wanted
                        self.assertEqual(runner.driver_warning_diagnostics(
                            output, 'source.f', str(self.root / 'source.f')), [])
                        with patch.object(runner, 'run', return_value=runner.ProcessResult(status, output)):
                            self.assertEqual(runner.check_fixture(fixture, comp).outcome, 'fail')
        for columns in ('0', '2-8'):
            output = f'source.f:2:{columns}:\n    2 | &\n      | 1\n' + wanted
            with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
                self.assertEqual(runner.check_fixture(fixture, comp).outcome, 'pass')

    def test_driver_attribution_does_not_parse_source_or_message_content_as_locations(self):
        raw = b'! source\n& ! note:7:\n'
        (self.root / 'source.f').write_bytes(raw)
        fixture = self.driver_reporting_fixture()
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        wanted = "f951: Warning: '&' not allowed by itself in line 2\n"
        for status in (0, 1):
            for continuation in (
                '    2 | & ! note:7:\n      | 1\n',
                "    2 | & ! other.f90:9:5-:\n      | 1\n",
                '',
            ):
                with self.subTest(status=status, continuation=continuation):
                    output = 'source.f:2:0:\n' + continuation + wanted
                    with patch.object(runner, 'run', return_value=runner.ProcessResult(status, output)):
                        result = runner.check_fixture(fixture, comp)
                    self.assertEqual(result.outcome, 'pass')
                    self.assertEqual(result.input_hashes['source.f'], hashlib.sha256(raw).hexdigest())
                    foreign = 'source.f:2:0:\n' + continuation + 'other.f90:9:5-:\n' + wanted
                    with patch.object(runner, 'run', return_value=runner.ProcessResult(status, foreign)):
                        self.assertEqual(runner.check_fixture(fixture, comp).outcome, 'fail')
        for message in ("expected token 'shape:3:2'", "expected token 'other.f90:9:5-:'"):
            for prefix in ('Error:', 'Warning:', 'f951: Warning:', 'f951: Fatal Error:'):
                output = f'{prefix} {message}\n' + wanted
                self.assertEqual(len(runner.driver_warning_diagnostics(
                    output, 'source.f', str(self.root / 'source.f'))), 1)

    def test_driver_attribution_rejects_severity_named_competing_files(self):
        fixture = self.driver_reporting_fixture()
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        wanted = "f951: Warning: '&' not allowed by itself in line 2\n"
        for filename in ('Error', 'Fatal Error', 'Warning', 'portability',
                         'f951: Warning', 'f951: Fatal Error', 'Error:asset',
                         'Error: asset', "Error: 'asset'", "Error: can't",
                         '|asset', '4 |asset'):
            for columns in ('1', '1-9', '5-', '5--8', '5-x', '5-8-9'):
                for status in (0, 1):
                    with self.subTest(filename=filename, columns=columns, status=status):
                        output = f'{filename}:9:{columns}:\n' + wanted
                        with patch.object(runner, 'run', return_value=runner.ProcessResult(status, output)):
                            self.assertEqual(runner.check_fixture(fixture, comp).outcome, 'fail')

    def test_declared_include_asset_may_have_a_severity_name(self):
        self.reporting_fixture()
        source = b"include 'Error'\n"
        payload = b'integer :: width\ninteger :: width\n'
        (self.root / 'source.f').write_bytes(source)
        (self.root / 'Error').write_bytes(payload)
        self.data['files'].append('Error')
        self.data['expect']['diagnostic'] = dict(
            file='Error', line=2, contains_any=["Symbol 'width' already declared"])
        fixture = self.fixture()
        output = "Error:2:1: Error: Symbol 'width' already declared\n"
        for family in ('gfortran', 'flang'):
            for status in (0, 1):
                with self.subTest(family=family, status=status):
                    comp = runner.Compiler(family, family, 'f2023')
                    with patch.object(runner, 'run', return_value=runner.ProcessResult(status, output)):
                        result = runner.check_fixture(fixture, comp)
                    self.assertEqual(result.outcome, 'pass')
                    self.assertEqual(result.input_hashes, {
                        'source.f': hashlib.sha256(source).hexdigest(),
                        'Error': hashlib.sha256(payload).hexdigest()})

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

    def test_qualified_warning_cannot_hide_a_later_native_internal_error(self):
        self.reporting_fixture()
        comp = runner.Compiler('flang', 'flang', 'f2018')
        for token in ('PUBLIC', 'PRIVATE', 'DEFERRED', 'NON_OVERRIDABLE', 'NOPASS', 'PASS'):
            warning = f"Attribute '{token}' cannot be used more than once [-Wredundant-attribute]"
            self.data['expect']['diagnostic'].update(
                contains_any=[warning],
                allow_nonfatal=[dict(compiler='flang', severity='warning', equals_any=[warning])])
            fixture = self.fixture()
            ordinary = f'source.f:2:7: warning: {warning}\n'
            for status in (0, 1):
                with self.subTest(token=token, status=status):
                    with patch.object(runner, 'run', return_value=runner.ProcessResult(status, ordinary)):
                        self.assertEqual(runner.check_fixture(fixture, comp).outcome, 'pass')
                    for origin in ('source.f:2:29: ', 'other.inc:8:1: ', ''):
                        output = ordinary + origin + "error: Internal: no symbol found for 'self'\n"
                        with patch.object(runner, 'run', return_value=runner.ProcessResult(status, output)):
                            result = runner.check_fixture(fixture, comp)
                        self.assertEqual(result.outcome, 'fail')
                        self.assertIn('compiler internal error', result.note)
                        self.assertEqual(result.output, output)

    def test_declared_included_cycle_report_is_matched_without_host_attribution(self):
        self.reporting_fixture()
        (self.root / 'loop.inc').write_text("include 'loop.inc'\n")
        self.data['files'].append('loop.inc')
        self.data['expect']['diagnostic'] = dict(
            file='loop.inc', line=1, contains_any=['being included recursively'])
        fixture = self.fixture()
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        actual = ("loop.inc:1:0:\n\n    1 | include 'loop.inc'\n"
                  "Fatal Error: File 'loop.inc' is being included recursively\n"
                  "compilation terminated.\n")
        for output, expected in (
            (actual, 'pass'),
            (actual.replace('loop.inc:1:0:', 'source.f:1:0:'), 'fail'),
            (actual.replace('loop.inc:1:0:', 'loop.inc:2:0:'), 'fail'),
            ("Fatal Error: File 'loop.inc' is being included recursively\n", 'fail'),
            ('loop.inc:1:0: error: INCLUDE nesting depth exceeded\n', 'fail'),
            (actual + 'internal compiler error: recursion crash\n', 'fail'),
        ):
            with self.subTest(output=output):
                with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
                    result = runner.check_fixture(fixture, comp)
                self.assertEqual(result.outcome, expected)
        with patch.object(runner, 'run', return_value=runner.ProcessResult(1, actual, timed_out=True)):
            self.assertEqual(runner.check_fixture(fixture, comp).outcome, 'fail')

    def test_lfortran_included_file_match_preserves_a_declared_subdirectory(self):
        self.reporting_fixture()
        (self.root / 'expected').mkdir()
        (self.root / 'expected/payload.inc').write_text('invalid\n')
        self.data['files'].append('expected/payload.inc')
        self.data['expect']['diagnostic'] = dict(file='expected/payload.inc', line=1)
        fixture = self.fixture()
        for filename, expected in (('expected/payload.inc', 'pass'), ('other/payload.inc', 'fail')):
            def transport(command, cwd, timeout, stdin=None):
                output = f'{Path(cwd).resolve() / filename}:1-1:1-7: syntax error: invalid input\n'
                return runner.ProcessResult(1, output)

            with self.subTest(filename=filename):
                with patch.object(runner, 'run', side_effect=transport):
                    result = runner.check_fixture(fixture, self.compiler)
                self.assertEqual(result.outcome, expected)

    def test_exact_diagnostic_selector_schema_and_unsupported_expectations(self):
        self.reporting_fixture()
        original = json.loads(json.dumps(self.data))
        for value in ([], '', None, {}, [None], [''], [' '], ['cause', 'cause'], ['cause', ' CAUSE ']):
            self.data = json.loads(json.dumps(original))
            self.data['expect']['diagnostic']['equals_any'] = value
            with self.subTest(value=value), self.assertRaises(SuiteError):
                self.fixture()
        self.data = json.loads(json.dumps(original))
        self.data['expect']['diagnostic'].update(contains_any=['cause'], equals_any=['cause'])
        with self.assertRaises(SuiteError):
            self.fixture()
        for phase, outcome in (('compile', 'success'), ('compile', 'reject'),
                               ('link', 'success'), ('link', 'reject'), ('run', 'success')):
            self.data = json.loads(json.dumps(original))
            self.data['expect'] = dict(
                phase=phase, outcome=outcome, step='source',
                diagnostic=dict(file='source.f', line=2, equals_any=['cause']))
            if phase != 'compile':
                self.data['link'] = dict(objects=['source.o'], output='program')
            with self.subTest(phase=phase, outcome=outcome), self.assertRaisesRegex(
                    SuiteError, 'compile-phase diagnose'):
                self.fixture()

    def test_exact_cause_nonfatal_codes_and_exclusions_use_actual_staging(self):
        self.reporting_fixture()
        cause = "'subject' has the wrong attribute"
        self.data['expect']['diagnostic'].update(
            equals_any=[cause, 'unsupported: ' + cause], excludes_any=['unsupported'],
            allow_nonfatal=[dict(compiler='flang', severity='portability', equals_any=[cause])])
        fixture = self.fixture()
        for family, mode in (('lfortran', 'f23'), ('gfortran', 'f2023'), ('flang', 'f2018')):
            for status in (0, 1, 2):
                for codes in (False, True):
                    for severity in ('error', 'warning', 'portability'):
                        for message in (cause, f'Unknown symbol "{cause}"', 'unsupported: ' + cause):
                            def transport(command, cwd, timeout, stdin=None):
                                source = Path(command[command.index('-c') + 1])
                                self.assertEqual(source.read_bytes(), self.raw)
                                if family == 'lfortran':
                                    text = f'{source}:2-2:1-80: semantic {severity} [R601]: {message}\n'
                                else:
                                    text = f'{source}:2:1: {severity}: {message}\n'
                                return runner.ProcessResult(status, text, stdout='', stderr=text)

                            expected = ('pass' if message == cause and (severity == 'error'
                                        or (family, severity) == ('flang', 'portability')) else 'fail')
                            with self.subTest(family=family, status=status, codes=codes,
                                              severity=severity, message=message), patch.object(
                                    runner, 'run', side_effect=transport):
                                check = runner.check_fixture(
                                    fixture, runner.Compiler(family, family, mode), codes=codes)
                            self.assertEqual(check.outcome, expected)
                            self.assertEqual((check.phase, len(check.trace)), ('compile', 1))
                            self.assertEqual(check.input_hashes, {'source.f': hashlib.sha256(self.raw).hexdigest()})

    def test_bound_included_extensionless_origins_and_primary_input_remain_distinct(self):
        self.reporting_fixture()
        (self.root / 'expected').mkdir()
        payload = b'integer :: subject, subject\n'
        (self.root / 'expected/Error').write_bytes(payload)
        self.data['files'].append('expected/Error')
        self.data['expect']['diagnostic'] = dict(file='expected/Error', line=1, equals_any=['duplicate subject'])
        fixture = self.fixture()
        for family, mode in (('lfortran', 'f23'), ('gfortran', 'f2023'), ('flang', 'f2018')):
            for origin, expected in (
                    ('expected/Error', 'pass'), ('./expected/Error', 'pass'), ('absolute', 'pass'),
                    ('alias', 'pass'), ('Error', 'fail'), ('other/Error', 'fail'), ('source.f', 'fail'),
                    ('../expected/Error', 'fail'), ('/foreign/expected/Error', 'fail')):
                def transport(command, cwd, timeout, stdin=None):
                    workspace = Path(cwd).resolve()
                    self.assertEqual(Path(command[command.index('-c') + 1]), workspace / 'source.f')
                    self.assertEqual((workspace / 'expected/Error').read_bytes(), payload)
                    location = origin
                    if origin == 'absolute':
                        location = str(workspace / 'expected/Error')
                    elif origin == 'alias':
                        (workspace / 'alias').symlink_to(workspace, target_is_directory=True)
                        location = str(workspace / 'alias/expected/Error')
                    if family == 'lfortran':
                        text = f'{location}:1-1:1-50: semantic error: duplicate subject\n'
                    else:
                        text = f'{location}:1:1: error: duplicate subject\n'
                    return runner.ProcessResult(0, text)

                with self.subTest(family=family, origin=origin), patch.object(runner, 'run', side_effect=transport):
                    check = runner.check_fixture(fixture, runner.Compiler(family, family, mode))
                self.assertEqual(check.outcome, expected)
                self.assertEqual(set(check.input_hashes), {'source.f', 'expected/Error'})

    def test_bound_reports_do_not_accept_echoes_quotes_or_missing_live_sources(self):
        self.reporting_fixture()
        self.data['expect']['diagnostic']['equals_any'] = ['actual cause']
        fixture = self.fixture()
        for family, mode in (('lfortran', 'f23'), ('gfortran', 'f2023'), ('flang', 'f2018')):
            for kind in ('source', 'caret', 'include', 'quoted', 'missing'):
                def transport(command, cwd, timeout, stdin=None):
                    source = Path(command[command.index('-c') + 1])
                    location = (f'{source}:2-2:1-40: semantic error: actual cause'
                                if family == 'lfortran' else f'{source}:2:1: error: actual cause')
                    text = dict(source=f' 2 | {location}', caret=f'   | ^ {location}',
                                include=f'In file included from {source}:2:1:\nerror: actual cause',
                                quoted=f'note: "{location}"', missing=location)[kind]
                    if kind == 'missing':
                        source.unlink()
                    return runner.ProcessResult(0, text)

                with self.subTest(family=family, kind=kind), patch.object(runner, 'run', side_effect=transport):
                    self.assertEqual(runner.check_fixture(
                        fixture, runner.Compiler(family, family, mode)).outcome, 'fail')

    def test_bound_driver_attribution_keeps_real_workspace_aliases_and_exact_gate(self):
        self.driver_reporting_fixture()
        self.data['expect']['diagnostic']['equals_any'] = ["'&' not allowed by itself"]
        fixture = self.fixture()
        comp = runner.Compiler('gfortran', 'gfortran', 'f2023')
        for foreign in (False, True):
            def transport(command, cwd, timeout, stdin=None):
                workspace = Path(cwd).resolve()
                (workspace / 'alias').symlink_to(workspace, target_is_directory=True)
                location = '/foreign/source.f' if foreign else str(workspace / 'alias/source.f')
                return runner.ProcessResult(
                    0, f"{location}:2:1:\nf951: Warning: '&' not allowed by itself in line 2\n")

            with self.subTest(foreign=foreign), patch.object(runner, 'run', side_effect=transport):
                self.assertEqual(runner.check_fixture(fixture, comp).outcome, 'fail' if foreign else 'pass')

    def disjoint_reporting_fixture(self):
        self.reporting_fixture()
        self.raw = (
            b'module eligibility_scope\n  implicit none\ncontains\n'
            b'  subroutine declaration_context(subject)\n    implicit none\n'
            b'    integer, contiguous :: subject(*)\n'
            b'  end subroutine declaration_context\nend module eligibility_scope\n')
        (self.root / 'source.f').write_bytes(self.raw)
        self.data['build'][0]['form'] = 'free'
        self.data['expect']['diagnostic'] = dict(
            file='source.f', line=6, equals_any=["'subject' has an ineligible attribute"],
            additional_spans=[dict(line=4)], excludes_any=['unsupported'],
            allow_nonfatal=[dict(compiler='flang', severity='portability',
                                equals_any=["'subject' has an ineligible attribute"])])
        return self.fixture()

    def test_additional_spans_are_nonempty_separate_and_source_bounded(self):
        self.disjoint_reporting_fixture()
        original = json.loads(json.dumps(self.data))
        for spans in ([], None, False, 4, {}, '4', [4], [None], [{}],
                      [dict(line=0)], [dict(line=True)], [dict(line='4')],
                      [dict(line=4, end_line=None)], [dict(line=4, end_line=True)],
                      [dict(line=4, end_line=3)], [dict(line=6)],
                      [dict(line=4, end_line=6)], [dict(line=4), dict(line=4, end_line=4)],
                      [dict(line=3, end_line=4), dict(line=4, end_line=5)],
                      [dict(line=10)], [dict(line=4, end_line=10)],
                      [dict(line=4, file='other.f')], [dict(line=4, contains_any=['other cause'])]):
            self.data = json.loads(json.dumps(original))
            self.data['expect']['diagnostic']['additional_spans'] = spans
            with self.subTest(spans=spans), self.assertRaises(SuiteError):
                self.fixture()
        self.data = json.loads(json.dumps(original))
        self.data['expect']['diagnostic']['additional_spans'] = [dict(line=9), dict(line=4)]
        before = json.loads(json.dumps(self.data['expect']['diagnostic']))
        self.assertEqual(self.fixture().expectation.diagnostic, before)
        self.data['expect']['diagnostic']['line'] = 10
        with self.assertRaises(SuiteError):
            self.fixture()
        for selector in ({}, {'contains_any': []}):
            self.data = json.loads(json.dumps(original))
            self.data['expect']['diagnostic'].pop('equals_any')
            self.data['expect']['diagnostic'].update(selector)
            with self.subTest(selector=selector), self.assertRaises(SuiteError):
                self.fixture()

    def test_additional_spans_reject_unsupported_success_reject_link_and_run(self):
        self.disjoint_reporting_fixture()
        original = json.loads(json.dumps(self.data))
        for phase, outcome in (('compile', 'success'), ('compile', 'reject'),
                               ('link', 'success'), ('link', 'reject'), ('run', 'success')):
            self.data = json.loads(json.dumps(original))
            self.data['expect'].update(phase=phase, outcome=outcome)
            self.data['expect']['diagnostic'].pop('equals_any')
            self.data['expect']['diagnostic']['contains_any'] = ['cause']
            if phase != 'compile':
                self.data['link'] = dict(objects=['source.o'], output='program')
            with self.subTest(phase=phase, outcome=outcome), self.assertRaisesRegex(
                    SuiteError, 'additional_spans requires compile-phase diagnose'):
                self.fixture()
        with self.assertRaisesRegex(SuiteError, 'additional_spans requires compile-phase diagnose'):
            runner.judge_rejection(runner.ProcessResult(1, 'error: cause'), self.compiler,
                                   runner.Metadata(), 'R601', diagnostic=dict(additional_spans=[dict(line=4)]))

    def test_disjoint_points_do_not_accept_a_gap_or_a_cross_anchor_range(self):
        fixture = self.disjoint_reporting_fixture()
        vectors = []
        for family, mode in (('lfortran', 'f23'), ('gfortran', 'f2023'), ('flang', 'f2018')):
            for code in (0, 1, 2):
                for codes in (False, True):
                    ranges = ((4, 4), (6, 6), (5, 5), (3, 3), (7, 7), (4, 6), (5, 6), (6, 5))
                    if family != 'lfortran':
                        ranges = tuple((line, line) for line in (3, 4, 5, 6, 7))
                    for first, last in ranges:
                        def transport(command, cwd, timeout, stdin=None):
                            source = Path(command[command.index('-c') + 1])
                            self.assertEqual(source.read_bytes(), self.raw)
                            message = "'subject' has an ineligible attribute"
                            severity = 'portability' if family == 'flang' else 'error'
                            text = (f'{source}:{first}-{last}:1-70: semantic {severity} [R601]: {message}\n'
                                    if family == 'lfortran' else f'{source}:{first}:1: {severity}: {message}\n')
                            return runner.ProcessResult(code, text, False, '', text, b'', text.encode())

                        with self.subTest(family=family, code=code, codes=codes, first=first, last=last), \
                                patch.object(runner, 'run', side_effect=transport):
                            check = runner.check_fixture(fixture, runner.Compiler(family, family, mode), codes=codes)
                        self.assertEqual(check.outcome, 'pass' if first == last and first in (4, 6) else 'fail')
                        self.assertEqual((check.phase, len(check.trace)), ('compile', 1))
                        self.assertEqual(check.input_hashes, {'source.f': hashlib.sha256(self.raw).hexdigest()})
                        vectors.append((family, code, codes, first, last))
        self.assertEqual(len(vectors), 108)

    def test_all_anchors_keep_cause_origin_nonfatal_code_and_native_failure_gates(self):
        fixture = self.disjoint_reporting_fixture()
        for line in (4, 6):
            for scenario in ('genuine', 'wrong-cause', 'quoted', 'foreign', 'warning', 'no-code',
                             'native', 'timeout', 'crash'):
                def transport(command, cwd, timeout, stdin=None):
                    source = Path(command[command.index('-c') + 1])
                    origin = '/foreign/source.f' if scenario == 'foreign' else str(source)
                    cause = "'subject' has an ineligible attribute"
                    if scenario == 'wrong-cause':
                        cause = "'other' has an ineligible attribute"
                    if scenario == 'quoted':
                        cause = 'Example: "' + cause + '"'
                    severity = 'warning' if scenario == 'warning' else 'error'
                    label = '' if scenario == 'no-code' else ' [R601]'
                    text = f'{origin}:{line}-{line}:1-70: semantic {severity}{label}: {cause}\n'
                    if scenario == 'native':
                        text += '/foreign/source.f:1-1:1-2: semantic error: Internal: failed\n'
                    return runner.ProcessResult(-11 if scenario == 'crash' else 0, text,
                                                scenario == 'timeout', '', text, b'', text.encode())

                with self.subTest(line=line, scenario=scenario), patch.object(runner, 'run', side_effect=transport):
                    check = runner.check_fixture(fixture, self.compiler, codes=True)
                self.assertEqual(check.outcome, 'pass' if scenario == 'genuine' else 'fail')

    def test_additional_spans_are_contained_individually_not_merged_when_adjacent(self):
        self.disjoint_reporting_fixture()
        self.data['expect']['diagnostic'].update(
            line=5, end_line=6, additional_spans=[dict(line=3, end_line=4)])
        fixture = self.fixture()
        for first, last, expected in ((3, 4, 'pass'), (5, 6, 'pass'), (4, 5, 'fail'), (3, 6, 'fail')):
            def transport(command, cwd, timeout, stdin=None):
                source = command[command.index('-c') + 1]
                text = (f"{source}:{first}-{last}:1-70: semantic error: "
                        "'subject' has an ineligible attribute\n")
                return runner.ProcessResult(0, text)
            with self.subTest(first=first, last=last), patch.object(runner, 'run', side_effect=transport):
                self.assertEqual(runner.check_fixture(fixture, self.compiler).outcome, expected)

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
                (self.compiler, 'source.f:2-2:1-20: syntax error [R601]: invalid token\n'),
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

    def test_point_rejection_does_not_accept_a_recovery_range(self):
        self.reporting_fixture()
        self.data['expect']['outcome'] = 'reject'
        self.data['expect']['diagnostic'].pop('allow_nonfatal')
        output = 'source.f:1-3:1-20: semantic error [R601]: unrelated recovery\n'
        with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
            self.assertEqual(runner.check_fixture(self.fixture(), self.compiler).outcome, 'fail')
        self.data['expect']['diagnostic'].update(line=1, end_line=2)
        with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
            self.assertEqual(runner.check_fixture(self.fixture(), self.compiler).outcome, 'fail')
        output = 'source.f:1-2:1-20: semantic error [R601]: declared statement\n'
        with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
            self.assertEqual(runner.check_fixture(self.fixture(), self.compiler).outcome, 'pass')

    def test_rejection_warning_uses_the_declared_point_or_span(self):
        self.reporting_fixture()
        self.data['expect']['outcome'] = 'reject'
        self.data['expect']['diagnostic'].pop('allow_nonfatal')
        self.data['reference_warnings'] = ['long-names']
        comp = runner.Compiler('flang', 'flang', 'f2018')
        output = 'source.f:1:7: portability: name too long [-Wlong-names]\n'
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
            self.assertEqual(runner.check_fixture(self.fixture(), comp).outcome, 'fail')
        self.data['expect']['diagnostic'].update(line=1, end_line=2)
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
            self.assertEqual(runner.check_fixture(self.fixture(), comp).outcome, 'pass')

    def test_rejection_predicate_matches_the_primary_diagnostic_not_echoed_text(self):
        self.reporting_fixture()
        self.data['expect']['outcome'] = 'reject'
        self.data['expect']['diagnostic'].pop('allow_nonfatal')
        self.data['expect']['diagnostic']['contains_any'] = ['names do not match']
        for comp, output in (
            (self.compiler, 'source.f:2-2:1-20: syntax error: unrelated\n! names do not match\n'),
            (self.compiler, 'source.f:1-1:1-20: syntax error: names do not match\n'
             'source.f:2-2:1-20: syntax error: unrelated\n'),
            (runner.Compiler('gfortran', 'gfortran', 'f2023'),
             'source.f:2:1: error: unrelated\n! names do not match\n'),
        ):
            with self.subTest(compiler=comp.family, output=output):
                with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
                    self.assertEqual(runner.check_fixture(self.fixture(), comp).outcome, 'fail')

    def test_semantic_predicate_rejects_same_line_unsupported_feature(self):
        self.reporting_fixture()
        self.data['expect']['diagnostic']['contains_any'] = [
            'does not reduce to a constant expression', 'must be constant',
            'cannot either be ASSUMED or DEFERRED']
        for message, expected in (
            ('Feature not implemented', 'fail'),
            ('Kind must be constant', 'pass'),
            ('Kind cannot either be ASSUMED or DEFERRED', 'pass'),
        ):
            with self.subTest(message=message):
                output = f'source.f:2-2:1-20: semantic error: {message}\n'
                with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
                    self.assertEqual(runner.check_fixture(self.fixture(), self.compiler).outcome,
                                     expected)

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
