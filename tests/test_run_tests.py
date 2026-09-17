import contextlib
import collections
import io
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import run_tests as runner

SHORT_NOTE_MESSAGES = (
    'note: example "semantic error: Internal: quoted only"',
    'semantic note: example "semantic error: Internal: quoted only"',
    'warning: example "semantic error: Internal: quoted only"',
    "note: example 'syntax error: Internal: quoted only'",
    'note: see nested.f90:7-7:1-60: semantic error: Internal: cited example',
)
SHORT_SEVERITY_HEADERS = (
    'semantic error', 'semantic\terror', 'semantic \terror', 'semantic\t error',
    'code-generation\tERROR', 'code_generation\terror', 'code generation\terror',
)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.lf = runner.Compiler('lfortran', 'lfortran', 'f23')

    def source(self, name, contents):
        path = self.root / name
        path.write_text(contents)
        return str(path)

    def test_timeout_with_pipe_held_outside_child_group_is_bounded_and_lossless(self):
        stdout_read, stdout_write = os.pipe()
        stderr_read, stderr_write = os.pipe()
        process = subprocess.Popen(
            [sys.executable, '-c', 'import time; time.sleep(10)'],
            stdin=subprocess.PIPE, stdout=stdout_write, stderr=stderr_write, start_new_session=True)
        process.stdout = os.fdopen(stdout_read, 'rb')
        process.stderr = os.fdopen(stderr_read, 'rb')
        stdout = b'partial stdout\xff\n'
        stderr = b'partial stderr\x00\n'
        os.write(stdout_write, stdout)
        os.write(stderr_write, stderr)
        old_handler = signal.getsignal(signal.SIGALRM)

        def expired(signum, frame):
            self.fail('post-timeout pipe draining exceeded its bound')

        try:
            signal.signal(signal.SIGALRM, expired)
            signal.setitimer(signal.ITIMER_REAL, 2)
            with patch.object(runner.subprocess, 'Popen', return_value=process):
                start = time.monotonic()
                result = runner.run(['synthetic-owned-process'], str(self.root), timeout=0.1)
            self.assertLess(time.monotonic() - start, 1)
            self.assertTrue(result.timed_out)
            self.assertEqual(result.stdout_bytes, stdout)
            self.assertEqual(result.stderr_bytes, stderr)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            os.close(stdout_write)
            os.close(stderr_write)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
            process.wait(timeout=2)

    def invalid(self, result, codes=False):
        source = 'subroutine s\n integer, save, save :: x ! {error C801 save}\nend subroutine\n'
        with patch.object(runner, 'run', return_value=result):
            return runner.check_invalid('C801_invalid.f90', source, 2, 'C801',
                                        (1, 3), self.lf, runner.Metadata(), codes)

    def test_canonical_ids(self):
        self.assertEqual(runner.canonical_rule('C15121'), 'C15121')
        self.assertEqual(runner.canonical_rule('S15_5_2_4'), 'S15.5.2.4')
        self.assertEqual(runner.canonical_rule('S10_2_1_3_001'), 'S10.2.1.3-001')

    def test_discovery_variants_and_repeatable_filters(self):
        self.source('C1401_valid__unnamed.f90', 'end\n')
        self.source('C601_valid.f90', 'end\n')
        self.source('C601_valid_helper.f90', 'module helper\nend module\n')
        self.source('S10_2_1_3_001_valid.f90', 'end\n')
        found = runner.discover(str(self.root), ['C1401', 'S10.2.1.3'])
        self.assertEqual([rule for _, rule, _ in found], ['C1401', 'S10.2.1.3-001'])
        self.assertEqual(len(runner.discover(str(self.root))), 3)

    def test_unmatched_filter_fails(self):
        self.source('C601_valid.f90', 'end\n')
        with self.assertRaises(runner.SuiteError):
            runner.discover(str(self.root), ['C601', 'typo'])

    def test_metadata(self):
        path = self.source('S10_2_1_3_023_valid.f90', '''! rule: S10.2.1.3-023
! covers: c-ptr-component
! evidence: context-only
! requires: coarray
! images: 2
program p
end program
''')
        meta = runner.metadata(path, 'S10.2.1.3-023')
        self.assertEqual(meta.facets, ['c-ptr-component'])
        self.assertEqual(meta.evidence, 'context-only')
        self.assertEqual(meta.images, 2)
        self.assertTrue(meta.coarray)

    def test_metadata_rejects_mismatched_rule(self):
        path = self.source('C601_valid.f90', '! rule: C602\nend\n')
        with self.assertRaises(runner.SuiteError):
            runner.metadata(path, 'C601')

    def test_metadata_rejects_unknown_profiles_and_duplicate_headers(self):
        for headers in ('! profile: typo\n', '! rule: C601\n! rule: C601\n'):
            path = self.source('C601_valid.f90', headers + 'end\n')
            with self.assertRaises(runner.SuiteError):
                runner.metadata(path, 'C601')

    def test_catalogue_case_requires_declared_coverage(self):
        path = self.source('S10_2_1_3_001_valid.f90', 'end\n')
        with self.assertRaises(runner.SuiteError):
            runner.metadata(path, 'S10.2.1.3-001')

    def test_explicit_main_program_cases_are_isolated(self):
        text = '''! rule: C1401
! case: first
program one
end program wrong ! {error C1401 first}
! case: second
program two
end program other ! {error C1401 second}
'''
        path = self.source('C1401_invalid.f90', text)
        first, second = list(runner.isolated_cases(path, 'C1401'))
        self.assertIn('program one', first[4])
        self.assertNotIn('program two', first[4])
        self.assertIn('program two', second[4])
        self.assertNotIn('program one', second[4])
        self.assertEqual(first[0], 4)
        self.assertEqual(second[0], 7)
        self.assertEqual(first[4].count('\n'), text.count('\n'))
        self.assertEqual(second[4].count('\n'), text.count('\n'))

    def test_legacy_isolation_keeps_shared_modules(self):
        path = self.source('C801_invalid.f90', '''module helper
 integer :: value
end module
subroutine a
 use helper
 integer, save, save :: x ! {error C801 a}
end subroutine
subroutine b
 use helper
 integer, save, save :: y ! {error C801 b}
end subroutine
''')
        cases = list(runner.isolated_cases(path, 'C801'))
        for case in cases:
            self.assertIn('module helper', case[4])
            self.assertEqual(case[4].count('use helper'), 1)
        self.assertNotIn('subroutine b', cases[0][4])
        self.assertNotIn('subroutine a', cases[1][4])

    def test_duplicate_cases_and_missing_markers_fail(self):
        for text in ('end\n', '''subroutine a
 integer :: x ! {error C801 duplicate}
 integer :: y ! {error C801 duplicate}
end subroutine
'''):
            path = self.source('C801_invalid.f90', text)
            with self.assertRaises(runner.SuiteError):
                list(runner.isolated_cases(path, 'C801'))

    def test_boundary_must_match_marker(self):
        path = self.source('C801_invalid.f90', '''! case: a
integer :: x ! {error C801 b}
end
''')
        with self.assertRaises(runner.SuiteError):
            list(runner.isolated_cases(path, 'C801'))

    def test_fixed_form_uses_explicit_boundaries(self):
        path = self.source('C1401_invalid.f', '''! case: wrong
      program p
      end program q ! {error C1401 wrong}
''')
        self.assertEqual(len(list(runner.isolated_cases(path, 'C1401'))), 1)

    def test_old_and_new_diagnostic_formats(self):
        text = '''case.f90:2-2:1-20: semantic error [C801]: repeated
case.f90:3-3:1-20: semantic error [E0231] (F2023 C801, C815): repeated
case.f90:4-4:1-20: semantic error [E0020] (F2023 S10.2.1.3-004): invalid
case.f90:5-5:1-20: semantic warning [C801]: repeated
'''
        errors = runner.lfortran_errors(text)
        self.assertEqual(errors[0].codes, {'C801'})
        self.assertEqual(errors[1].codes, {'E0231', 'C801', 'C815'})
        self.assertIn('S10.2.1.3-004', errors[2].codes)
        self.assertEqual([error.first for error in errors], [2, 3, 4])

    def test_unqualified_recovery_range_does_not_satisfy_a_point(self):
        result = runner.ProcessResult(1, 'case.f90:1-3:1-20: syntax error [C801]: repeated')
        self.assertEqual(self.invalid(result, True).outcome, 'fail')

    def test_large_diagnostic_ranges_are_not_expanded(self):
        errors = runner.lfortran_errors('case.f90:1-1000000000:1-20: syntax error: invalid')
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].last, 1000000000)

    def test_invalid_reported_ranges_are_not_source_locations(self):
        for span in ('0-2', '3-2'):
            with self.subTest(span=span):
                self.assertEqual(runner.lfortran_errors(
                    f'case.f90:{span}:1-20: syntax error: invalid'), [])

    def test_resource_failure_detection_does_not_scan_application_data(self):
        result = runner.ProcessResult(0, 'f951: Fatal Error: Out of memory\n')
        self.assertEqual(runner.failure(result, 'compile').outcome, 'fail')
        self.assertIsNone(runner.failure(result, 'run', compiler_process=False))

    def test_native_internal_error_is_a_compiler_failure_at_any_normal_status(self):
        for output in (
            "source.f90:2:29: error: Internal: no symbol found for 'self'\n",
            "source.f90:2:5-29: fatal error: Internal: no symbol found for 'self'\n",
            "payload.inc:2:29: error: Internal: no symbol found for 'self'\n",
            "payload:2:29: error: Internal: no symbol found for 'self'\n",
            "error: Internal: no symbol found for 'self'\n",
            "source.f90:2:29:\nError: Internal: no symbol found for 'self'\n",
        ):
            for status in (0, 1):
                with self.subTest(output=output, status=status):
                    result = runner.ProcessResult(status, output)
                    check = runner.failure(result, 'compile')
                    self.assertEqual(check.outcome, 'fail')
                    self.assertIn('compiler internal error', check.note)
                    self.assertEqual(check.output, output)
                    self.assertIsNone(runner.failure(result, 'run', compiler_process=False))

    def test_native_internal_error_detection_uses_message_not_source_or_filename(self):
        for output in (
            "    2 | error: Internal: no symbol found for 'self'\n",
            "      | error: Internal: no symbol found for 'self'\n",
            "error: Internal:2:29: error: ordinary source error\n",
            "prefix error: Internal: source.f90:2:29: error: ordinary source error\n",
            "source.f90:2:29: error: Unknown symbol 'error: Internal:'\n",
            "Error: Unknown symbol 'error: Internal:'\n",
            "Error: token 'source.f90:2:29: error: Internal:' is not valid\n",
            "source.f90:2:29: warning: Internal: optional advisory\n",
            "note: compiler output can contain error: Internal: messages\n",
        ):
            with self.subTest(output=output):
                self.assertIsNone(runner.failure(runner.ProcessResult(1, output), 'compile'))

    def test_short_internal_errors_fail_at_every_ordinary_status(self):
        for output in (
            "source.f90:4-4:1-60: semantic error: Internal: duplicate attribute\n",
            "source.f90:4-5:1-60: syntax error [E0123] (F2023 C801): Internal: duplicate attribute\n",
            "payload.inc:4-4:1-60: code generation error: internal: unexpected node\n",
            "payload:4-4:1-60: SEMANTIC ERROR: INTERNAL: unexpected node\n",
        ):
            for status in (0, 1, 2):
                with self.subTest(output=output, status=status):
                    result = runner.ProcessResult(status, output)
                    check = runner.failure(result, 'compile')
                    self.assertEqual(check.outcome, 'fail')
                    self.assertIn('compiler internal error', check.note)
                    self.assertEqual(check.output, output)
                    self.assertIsNone(runner.failure(result, 'run', compiler_process=False))

    def test_short_internal_detection_preserves_message_location_and_content_boundaries(self):
        short = "source.f90:4-4:1-60: semantic error: Internal: duplicate attribute"
        for output in (
            "  4 | " + short,
            "    | " + short,
            "In file included from " + short,
            "error: Internal:4-4:1-60: semantic error: ordinary source error",
            "dir/Internal: source.f90:4-4:1-60: semantic error: ordinary source error",
            "source.f90:4-4:1-60: semantic warning: Internal: optional advisory",
            "source.f90:4-4:1-60: semantic error: Unknown symbol 'Internal: duplicate attribute'",
            "Error: token '" + short + "' is not valid",
            'Warning: example "' + short + '" is only content',
            "f951: Error: token '" + short + "' is not valid",
            "prefix:2:3:source.f90:4-4:1-60: semantic error: Internal: duplicate attribute",
            "source.f90:4-4:1-60: semantic error: Internal:   ",
        ):
            with self.subTest(output=output):
                self.assertIsNone(runner.failure(runner.ProcessResult(1, output), 'compile'))

    def test_short_internal_wrapper_cannot_satisfy_a_diagnose_cause(self):
        compiler = runner.Compiler('mock-lfortran', 'lfortran', 'f23')
        diagnostic = dict(file='source.f90', line=4, end_line=4,
                          contains_any=["Automatic object 'text' at (1) cannot have the SAVE attribute"])
        message = diagnostic['contains_any'][0]
        for status in (0, 1, 2):
            for prefix, expected in (('', 'pass'), ('Internal: ', 'fail')):
                with self.subTest(status=status, prefix=prefix):
                    output = f'source.f90:4-4:1-60: semantic error: {prefix}{message}\n'
                    check = runner.judge_diagnostic(
                        runner.ProcessResult(status, output), compiler, 'C814', diagnostic)
                    self.assertEqual(check.outcome, expected)

    def test_short_notes_do_not_promote_payloads_to_compiler_errors(self):
        for message in SHORT_NOTE_MESSAGES:
            output = 'source.f90:4-4:1-60: ' + message + '\n'
            for status in (0, 1, 2):
                for phase in ('compile', 'link', 'version query'):
                    with self.subTest(message=message, status=status, phase=phase):
                        result = runner.ProcessResult(status, output)
                        self.assertIsNone(runner.failure(result, phase))
                        self.assertIsNone(runner.failure(result, 'run', compiler_process=False))
            actual = output + 'source.f90:5-5:1-60: semantic error: Internal: actual failure\n'
            self.assertEqual(runner.failure(runner.ProcessResult(0, actual), 'compile').outcome, 'fail')

    def test_short_note_payloads_do_not_replace_an_actual_judge_cause(self):
        diagnostic = dict(file='source.f90', line=4, end_line=4, contains_any=['selected cause'])
        cause = 'source.f90:4-4:1-60: semantic error [C801]: selected cause\n'
        for message in SHORT_NOTE_MESSAGES:
            note = 'source.f90:4-4:1-60: ' + message + '\n'
            for status in (0, 1, 2):
                for codes in (False, True):
                    with self.subTest(message=message, status=status, codes=codes):
                        result = runner.ProcessResult(status, cause + note)
                        diagnosed = runner.judge_diagnostic(result, self.lf, 'C801', diagnostic, codes=codes)
                        self.assertEqual(diagnosed.outcome, 'pass')
                        rejected = runner.judge_rejection(
                            result, self.lf, runner.Metadata(), 'C801', line=4, diagnostic=diagnostic, codes=codes)
                        self.assertEqual(rejected.outcome, 'pass' if status else 'fail')
                        only_note = note.replace('quoted only', 'selected cause')
                        self.assertEqual(runner.judge_diagnostic(
                            runner.ProcessResult(status, only_note), self.lf, 'C801', diagnostic).outcome, 'fail')

    def test_short_note_payloads_do_not_fail_a_successful_version_query(self):
        for message in SHORT_NOTE_MESSAGES:
            output = 'LFortran version: synthetic probe\nsource.f90:4-4:1-60: ' + message + '\n'
            with self.subTest(message=message), patch.object(
                    runner, 'run', return_value=runner.ProcessResult(0, output)):
                compiler = runner.compiler('synthetic-lfortran', True, 'f23', [], 1)
                self.assertEqual(compiler.version, 'LFortran version: synthetic probe')

    def test_short_severity_separators_have_consistent_guard_and_judge_meaning(self):
        diagnostic = dict(file='source.f90', line=4, end_line=4, contains_any=['selected cause'])
        for header in SHORT_SEVERITY_HEADERS:
            for status in (0, 1, 2):
                for prefix in ('', 'Internal: '):
                    text = f'source.f90:4-4:1-60: {header} [C801] (F2023 C801): {prefix}selected cause\n'
                    with self.subTest(header=header, status=status, prefix=prefix):
                        parsed = runner.lfortran_diagnostics(text)
                        self.assertEqual(len(parsed), 1)
                        self.assertEqual(parsed[0].severity, 'error')
                        result = runner.ProcessResult(status, text)
                        for phase in ('compile', 'link', 'version query'):
                            self.assertEqual(runner.failure(result, phase) is not None, bool(prefix))
                        self.assertIsNone(runner.failure(result, 'run', compiler_process=False))
                        for codes in (False, True):
                            self.assertEqual(runner.judge_diagnostic(
                                result, self.lf, 'C801', diagnostic, codes=codes).outcome,
                                'fail' if prefix else 'pass')
                            self.assertEqual(runner.judge_rejection(
                                result, self.lf, runner.Metadata(), 'C801', line=4,
                                diagnostic=diagnostic, codes=codes).outcome,
                                'pass' if status and not prefix else 'fail')

    def test_short_extraction_cannot_borrow_quoted_inner_location(self):
        diagnostic = dict(file='source.f90', line=4, end_line=4, contains_any=['selected cause'])
        actual = 'source.f90:4-4:1-60: semantic error [C801]: selected cause\n'
        for category in ('note', 'semantic note', 'warning'):
            for filename in ('examples/source.f90', '/example/source.f90'):
                for quote in ('"', "'"):
                    text = (f'source.f90:9-9:1-60: {category}: example {quote}'
                            f'{filename}:4-4:1-60: semantic error [C801]: selected cause{quote}\n')
                    for status in (0, 1, 2):
                        for codes in (False, True):
                            with self.subTest(category=category, filename=filename,
                                              quote=quote, status=status, codes=codes):
                                self.assertEqual(runner.lfortran_diagnostics(text), [])
                                result = runner.ProcessResult(status, text)
                                self.assertEqual(runner.judge_diagnostic(
                                    result, self.lf, 'C801', diagnostic, codes=codes).outcome, 'fail')
                                self.assertEqual(runner.judge_rejection(
                                    result, self.lf, runner.Metadata(), 'C801', line=4,
                                    diagnostic=diagnostic, codes=codes).outcome, 'fail')
                                self.assertEqual(runner.judge_diagnostic(
                                    runner.ProcessResult(status, text + actual), self.lf,
                                    'C801', diagnostic, codes=codes).outcome, 'pass')
        self.assertEqual(runner.lfortran_diagnostics('Error: quoted "' + actual.rstrip() + '"\n'), [])
        self.assertEqual(runner.lfortran_diagnostics('  4 | ' + actual), [])
        self.assertEqual(runner.lfortran_diagnostics('In file included from ' + actual), [])

    def test_tab_internal_cannot_pass_compiler_version_discovery(self):
        for header in SHORT_SEVERITY_HEADERS:
            output = ('LFortran version: synthetic probe\n'
                      f'source.f90:4-4:1-60: {header}: Internal: actual failure\n')
            with self.subTest(header=header), patch.object(
                    runner, 'run', return_value=runner.ProcessResult(0, output)):
                with self.assertRaisesRegex(runner.SuiteError, 'version query failed'):
                    runner.compiler('synthetic-lfortran', True, 'f23', [], 1)

    def test_unlocated_message_prefixes_shield_quoted_diagnostic_examples(self):
        diagnostic = dict(file='source.f90', line=4, end_line=4, contains_any=['selected cause'])
        actual = 'source.f90:4-4:1-60: semantic error [C801]: selected cause\n'
        prefixes = ('note:', 'semantic note:', 'remark:', 'help:', 'semantic warning:',
                    'semantic error [C801] (F2023 C801):', 'compiler-driver: note:', 'f951: note:')
        for prefix in prefixes:
            for quote in ('"', "'"):
                text = prefix + ' example ' + quote + (
                    'examples/source.f90:4-4:1-60: semantic error: Internal: selected cause') + quote + '\n'
                for status in (0, 1, 2):
                    with self.subTest(prefix=prefix, quote=quote, status=status):
                        self.assertIsNone(runner.reference_location_header(text))
                        self.assertEqual(runner.lfortran_diagnostics(text), [])
                        self.assertIsNone(runner.failure(runner.ProcessResult(status, text), 'compile'))
                        self.assertEqual(runner.judge_diagnostic(
                            runner.ProcessResult(status, text), self.lf, 'C801', diagnostic).outcome, 'fail')
                        self.assertEqual(runner.judge_diagnostic(
                            runner.ProcessResult(status, text + actual), self.lf, 'C801',
                            diagnostic, codes=True).outcome, 'pass')
                unquoted = prefix + 'examples/source.f90:4-4:1-60: semantic error: Internal: actual failure\n'
                self.assertTrue(runner.native_internal_error(unquoted))

    def test_successful_exit_does_not_count_as_rejection(self):
        result = runner.ProcessResult(0, 'case.f90:2-2:1-20: semantic error [C801]: repeated')
        self.assertEqual(self.invalid(result).outcome, 'fail')

    def test_crash_after_expected_error_does_not_pass(self):
        result = runner.ProcessResult(-11, 'case.f90:2-2:1-20: semantic error [C801]: repeated')
        self.assertEqual(self.invalid(result).outcome, 'fail')

    def test_shell_encoded_signal_does_not_pass(self):
        result = runner.ProcessResult(139, 'case.f90:2-2:1-20: semantic error [C801]: repeated')
        self.assertEqual(self.invalid(result).outcome, 'fail')

    def test_internal_error_exit_one_does_not_pass(self):
        result = runner.ProcessResult(1, 'case.f90:2-2:1-20: semantic error [C801]: repeated\n'
                                      'LCOMPILERS_ASSERT failed')
        self.assertEqual(self.invalid(result).outcome, 'fail')

    def test_verifier_failure_is_not_a_language_diagnostic(self):
        result = runner.ProcessResult(1, 'case.f90:2-2:1-20: ASR verify pass error [C801]: invalid IR')
        self.assertEqual(self.invalid(result).outcome, 'fail')

    def test_standard_reference_satisfies_codes_mode(self):
        result = runner.ProcessResult(1, 'case.f90:2-2:1-20: semantic error [E1] (F2023 C801): repeated')
        self.assertEqual(self.invalid(result, True).outcome, 'pass')

    def test_isolated_cases_do_not_require_error_recovery(self):
        result = runner.ProcessResult(1, 'case.f90:2-2:1-20: syntax error [C801]: repeated')
        with patch.object(runner, 'run', return_value=result) as run:
            runner.check_invalid('C801_invalid.f90', 'end\n', 2, 'C801',
                                 (1, 3), self.lf, runner.Metadata())
        self.assertNotIn('--continue-compilation', run.call_args[0][0])

    def test_unrelated_rule_code_does_not_pass_codes_mode(self):
        result = runner.ProcessResult(1, 'case.f90:2-2:1-20: semantic error [C815]: repeated')
        self.assertEqual(self.invalid(result, True).outcome, 'fail')

    def test_reference_locations(self):
        text = 'case.f90:4:8:\n    4 | invalid\nError: invalid\ncase.f90:8:2: error: invalid\n'
        self.assertEqual(runner.reference_error_lines(text), {4, 8})

    def test_malformed_reference_locations_clear_prior_attribution(self):
        for filename in (None, 'case.f90', 'payload.inc'):
            source = filename or 'case.f90'
            for origin in (source, 'other.f90', 'other.inc'):
                for columns in ('5-', '5--8', '5-x', '5-8-9', '8-5', '0-8'):
                    with self.subTest(filename=filename, origin=origin, columns=columns):
                        text = f'{source}:4:1:\n{origin}:9:{columns}:\nError: invalid\n'
                        self.assertEqual(runner.reference_error_lines(text, filename), set())
                        restored = text + f'{source}:7:2-8:\n    7 | invalid\n      |  1\nError: invalid\n'
                        self.assertEqual(runner.reference_error_lines(restored, filename), {7})
            text = f'{source}:4:1:\n{source}:9-10:5-8:\nError: invalid\n'
            self.assertEqual(runner.reference_error_lines(text, filename), set())

    def test_reference_record_content_is_not_a_location_header(self):
        for filename in (None, 'source.f90', 'payload.inc', 'payload'):
            source = filename or 'source.f90'
            for columns in ('0', '1', '1-9'):
                for continuation in (
                    '    4 | value = values(1:3:2)\n      | 1\n',
                    '    4 | integer, len :: width ! stamp:9:\n      | 1\n',
                    "    4 | print *, 'other.f90:9:5-:'\n      | 1\n",
                    '      | shape:3:2\n',
                    '',
                ):
                    for severity in ('Error', 'Fatal Error', 'Warning', 'portability'):
                        with self.subTest(filename=filename, columns=columns,
                                          continuation=continuation, severity=severity):
                            message = "expected token 'shape:3:2'"
                            output = f'{source}:4:{columns}:\n' + continuation
                            output += f'{severity}: {message}\n'
                            self.assertEqual(list(runner.reference_messages(output, filename)),
                                             [(4, severity.lower(), message)])
                            foreign = f'{source}:4:{columns}:\n' + continuation
                            foreign += f'other.f90:9:5-:\n{severity}: {message}\n'
                            self.assertEqual(list(runner.reference_messages(foreign, filename)), [])

    def test_severity_names_remain_declared_or_competing_filenames(self):
        for filename in ('Error', 'Fatal Error', 'Warning', 'portability',
                         'Error:asset', 'Error: asset', "Error: 'asset'", "Error: can't",
                         '|asset', '4 |asset'):
            for columns in ('0', '1', '1-9'):
                for tail in (' Error: wanted\n', '\nError: wanted\n'):
                    with self.subTest(filename=filename, columns=columns, tail=tail):
                        output = f'{filename}:9:{columns}:' + tail
                        self.assertEqual(list(runner.reference_messages(output, filename)),
                                         [(9, 'error', 'wanted')])
                        self.assertEqual(list(runner.reference_messages(
                            'source.f90:5:1:\n' + output, 'source.f90')), [])
                        self.assertEqual(list(runner.reference_messages(
                            'source.f90:5:1:\n' + output)), [])
            for columns in ('5-', '5--8', '5-x', '5-8-9', '8-5', '0-8'):
                for tail in (' Error: wanted\n', '\nError: wanted\n'):
                    with self.subTest(filename=filename, columns=columns, tail=tail):
                        output = f'source.f90:5:1:\n{filename}:9:{columns}:' + tail
                        self.assertEqual(list(runner.reference_messages(output, 'source.f90')), [])
                        self.assertEqual(list(runner.reference_messages(output, filename)), [])
        for message in ('invalid', "expected token 'shape:3:2'"):
            self.assertEqual(list(runner.reference_messages(
                'source.f90:5:1:\nError:' + message, 'source.f90')), [(5, 'error', message)])

    def test_ambiguous_unquoted_coordinates_cannot_borrow_a_location(self):
        for message in (
            'Error: shape:3:2: Error: wanted',
            'Error: shape:3:5-: Error: wanted',
            'Warning: shape:3:2:',
        ):
            output = 'source.f90:5:1:\n' + message + '\nError: wanted\n'
            self.assertEqual(list(runner.reference_messages(output, 'source.f90')), [])
            self.assertEqual(runner.driver_warning_diagnostics(
                message + '\nf951: Warning: wanted in line 5\n',
                'source.f90', '/tmp/source.f90'), [])

    def test_reference_extraction_cannot_switch_coordinate_candidates(self):
        quoted = 'Error: "/tmp/source.f90:5:1: Error: wanted"'
        for columns in ('1', '1-9', '5-', '5--8', '5-x', '5-8-9'):
            for prefix in ('', 'source.f90:4:1:\n'):
                with self.subTest(columns=columns, prefix=prefix):
                    output = prefix + quoted + f' other.f90:9:{columns}:\n'
                    self.assertEqual(list(runner.reference_messages(output, 'source.f90')), [])
                    self.assertEqual(list(runner.reference_messages(output)), [])
                    self.assertEqual(runner.driver_warning_diagnostics(
                        output + 'f951: Warning: wanted in line 5\n',
                        'source.f90', '/tmp/source.f90'), [])
        for columns in ('5-', '5--8', '5-x', '5-8-9'):
            output = f'/tmp/other.f90:9:{columns}: /tmp/source.f90:5:1: Error: wanted\n'
            self.assertEqual(list(runner.reference_messages(output, 'source.f90')), [])
            self.assertEqual(list(runner.reference_messages(output)), [])

    def test_declared_include_locations_are_not_limited_by_suffix(self):
        for filename in ('loop.inc', 'payload.data', 'payload', 'nested/payload.inc'):
            with self.subTest(filename=filename):
                text = (f'{filename}:1:0:\n\n    1 | include text\n'
                        "Fatal Error: File 'payload' is being included recursively\n")
                self.assertEqual(runner.reference_error_lines(text, filename), {1})
                inline = f'/workspace/{filename}:2:7: error: invalid included source\n'
                self.assertEqual(runner.reference_error_lines(inline, filename), {2})
                self.assertEqual(runner.reference_error_lines(text, 'other.inc'), set())
        self.assertEqual(runner.reference_error_lines(
            'f951:1:2: error: driver-only text\n', 'loop.inc'), set())
        self.assertEqual(runner.reference_error_lines(
            'payload:1:2: error: no declared input\n'), set())

    def test_declared_input_paths_do_not_collapse_to_the_same_basename(self):
        text = '/workspace/other/payload.inc:3:1: error: wrong input\n'
        self.assertEqual(runner.reference_error_lines(text, 'expected/payload.inc'), set())
        self.assertEqual(runner.reference_error_lines(text, 'other/payload.inc'), {3})
        self.assertFalse(runner.diagnostic_filename_matches('source.f90', ''))

    def test_include_contexts_do_not_lend_locations_to_driver_errors(self):
        for context in (
            'In file included from /workspace/payload.inc:1:0:',
            '                 from parent.f90:2:',
            'payload.inc:1:0: included here',
            'payload.inc:1:0: note: included here',
            'other.data:1:0:',
        ):
            with self.subTest(context=context):
                text = 'payload.inc:1:0:\n' + context + '\nFatal Error: unrelated driver failure\n'
                self.assertEqual(runner.reference_error_lines(text, 'payload.inc'), set())

    def test_warning_location_is_not_reused_for_an_unlocated_error(self):
        text = 'case.f90:4:8:\nWarning: unrelated\nError: driver failed without a location\n'
        self.assertEqual(runner.reference_error_lines(text), set())

    def test_context_location_is_not_reused_for_an_unlocated_error(self):
        text = 'case.f90:4:8: in the context: statement\nError: driver failed\n'
        self.assertEqual(runner.reference_error_lines(text), set())

    def test_inline_negative_reports_retain_trace_and_staged_input_hash(self):
        source = 'end\n'
        output = 'case.f90:1-1:1-3: syntax error [C801]: invalid\n'
        with patch.object(runner, 'run', return_value=runner.ProcessResult(1, output)):
            result = runner.check_invalid('C801_invalid.f90', source, 1, 'C801',
                                          (1, 1), self.lf, runner.Metadata())
        self.assertEqual(result.outcome, 'pass')
        self.assertEqual(result.trace[0]['phase'], 'compile')
        self.assertEqual(result.trace[0]['returncode'], 1)
        self.assertEqual(result.input_hashes, {
            'C801_invalid.f90': runner.hashlib.sha256(source.encode()).hexdigest()})

    def test_reference_labels_preserve_execution_phase(self):
        for phase, expected in (('compile', 'compiles'), ('link', 'links'), ('run', 'runs'), ('', 'passes')):
            with self.subTest(phase=phase):
                self.assertEqual(runner.reference_label(runner.Check('pass', phase=phase), 'valid'),
                                 expected)

    def test_unlocated_reference_failure_is_not_acceptance(self):
        comp = runner.Compiler('flang', 'flang', 'f2018')
        with patch.object(runner, 'run', return_value=runner.ProcessResult(1, 'fatal error: aborted')):
            check = runner.check_invalid('C601_invalid.f90', 'end\n', 1, 'C601',
                                         (1, 1), comp, runner.Metadata())
        self.assertEqual(check.outcome, 'fail')
        self.assertIn('without a located case diagnostic', check.note)

    def test_explicit_reference_warning_can_corroborate_a_violation(self):
        comp = runner.Compiler('flang', 'flang', 'f2018')
        output = 'case.f90:2:16: portability: name too long [-Wlong-names]\n'
        meta = runner.Metadata(reference_warnings=['long-names'])
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
            check = runner.check_invalid('C601_invalid.f90', 'end\n', 2, 'C601',
                                         (1, 3), comp, meta)
        self.assertEqual(check.outcome, 'pass')
        self.assertEqual(runner.reference_label(check, 'invalid'), 'diagnoses')

    def test_unrelated_or_unapproved_warning_does_not_corroborate_a_violation(self):
        comp = runner.Compiler('flang', 'flang', 'f2018')
        output = 'case.f90:2:16: portability: name too long [-Wlong-names]\n'
        for allowed, bounds in (([], (1, 3)), (['unused-variable'], (1, 3)), (['long-names'], (4, 8))):
            with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
                check = runner.check_invalid('C601_invalid.f90', 'end\n', 2, 'C601',
                                             bounds, comp, runner.Metadata(reference_warnings=allowed))
            self.assertEqual(check.outcome, 'fail')

    def test_reference_warning_policy_does_not_relax_lfortran(self):
        output = 'case.f90:2:16: portability: name too long [-Wlong-names]\n'
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, output)):
            check = runner.check_invalid('C601_invalid.f90', 'end\n', 2, 'C601', (1, 3),
                                         self.lf, runner.Metadata(reference_warnings=['long-names']))
        self.assertEqual(check.outcome, 'fail')

    def test_valid_exit_77_is_a_failure_not_an_implicit_skip(self):
        with patch.object(runner, 'run', side_effect=[
                runner.ProcessResult(0, ''), runner.ProcessResult(77, 'ERROR STOP 77')]):
            check = runner.check_valid('C601_valid.f90', self.lf, runner.Metadata())
        self.assertEqual(check.outcome, 'fail')

    def test_optional_profile_can_explicitly_skip(self):
        with patch.object(runner, 'run', side_effect=[
                runner.ProcessResult(0, ''), runner.ProcessResult(77, 'STOP 77')]) as run:
            check = runner.check_valid('case.f90', self.lf,
                                       runner.Metadata(profiles=['iso10646']))
        self.assertEqual(check.outcome, 'skip')
        self.assertEqual(run.call_count, 2)

    def test_failed_profile_is_not_a_success_shaped_skip(self):
        with patch.object(runner, 'run', return_value=runner.ProcessResult(1, 'error: unsupported')):
            check = runner.profile_check(self.lf, 'iso10646', 1)
        self.assertEqual(check.outcome, 'fail')

    def test_profile_evidence_is_recorded_without_mutating_cached_results(self):
        case = runner.SuiteCase(
            'case', 'C601', 'valid', 'not-compiled.f90',
            runner.Metadata(profiles=['iso10646', 'two-integer-kinds']), 'case')
        with patch.object(runner, 'run', side_effect=[
                runner.ProcessResult(0, ''), runner.ProcessResult(77, 'STOP 77')]) as run:
            first = runner.execute_case(case, self.lf)
            second = runner.execute_case(case, self.lf)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(first.outcome, 'skip')
        self.assertEqual(first.trace, [])
        self.assertEqual(first.input_hashes, {})
        profile = first.profile_checks['iso10646']
        self.assertEqual(profile['outcome'], 'skip')
        self.assertEqual([item['phase'] for item in profile['trace']],
                         ['profile-compile', 'profile-run'])
        self.assertEqual(profile['trace'][-1]['returncode'], 77)
        self.assertTrue(profile['input_hashes'])
        self.assertNotIn('profile_checks', profile)
        self.assertEqual(first.profile_checks['two-integer-kinds']['outcome'], 'not-run')
        self.assertEqual(first.profile_checks, second.profile_checks)
        self.assertEqual(self.lf.profiles['iso10646'].profile_checks, {})

    def test_successful_case_keeps_profile_and_program_traces_separate(self):
        path = self.source('C601_valid.f90', 'program p\nend program\n')
        case = runner.SuiteCase('case', 'C601', 'valid', path,
                                runner.Metadata(profiles=['iso10646']), 'case')
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, '')):
            result = runner.execute_case(case, self.lf)
        self.assertEqual(result.outcome, 'pass')
        self.assertEqual([item['phase'] for item in result.trace], ['compile-link', 'run'])
        self.assertEqual(result.profile_checks['iso10646']['outcome'], 'pass')
        self.assertEqual([item['phase'] for item in result.profile_checks['iso10646']['trace']],
                         ['profile-compile', 'profile-run'])

    def test_missing_launcher_does_not_pass_a_multi_image_case(self):
        meta = runner.Metadata(coarray=True, images=2)
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, '')) as run:
            check = runner.check_valid('case.f90', self.lf, meta)
        self.assertEqual(check.outcome, 'skip')
        self.assertEqual(check.phase, 'launch')
        self.assertEqual(run.call_count, 1)

    def test_launcher_is_an_argument_vector_not_a_shell_command(self):
        self.lf.launcher = ['launch', '-n', '{images}', '{exe}']
        with patch.object(runner, 'run', return_value=runner.ProcessResult(0, '')) as run:
            check = runner.check_valid('case.f90', self.lf, runner.Metadata(coarray=True, images=2))
        self.assertEqual(check.outcome, 'pass')
        self.assertEqual(run.call_args[0][0][:3], ['launch', '-n', '2'])

    def test_timeout_is_bounded_and_reported(self):
        start = time.monotonic()
        result = runner.run([sys.executable, '-c', 'import time; time.sleep(30)'],
                            str(self.root), timeout=0.05)
        self.assertTrue(result.timed_out)
        self.assertLess(time.monotonic() - start, 5)
        self.assertEqual(runner.failure(result, 'execution').outcome, 'fail')

    def test_missing_executable_is_a_harness_error(self):
        check = runner.safely(runner.run, ['/nonexistent/conformance-compiler'], str(self.root), 1)
        self.assertEqual(check.outcome, 'error')
        self.assertEqual(runner.status('case', check, {'case'}), 'ERROR')

    def test_skips_do_not_become_xpass(self):
        self.assertEqual(runner.status('case', runner.Check('skip'), {'case'}), 'SKIP')

    def test_xfail_update_preserves_unrun_skipped_and_error_entries(self):
        path = self.source('xfail.txt', 'unrun  # old\nskipped  # old\nbroken  # old\nfixed  # old\n')
        results = [
            {'name': 'skipped', 'check': runner.Check('skip'), 'review': runner.Review('source-reviewed')},
            {'name': 'broken', 'check': runner.Check('error'), 'review': runner.Review('source-reviewed')},
            {'name': 'fixed', 'check': runner.Check('pass'), 'review': runner.Review('source-reviewed')},
            {'name': 'new', 'check': runner.Check('fail', 'reason'), 'review': runner.Review('source-reviewed')},
        ]
        runner.update_xfail(path, results)
        self.assertEqual(Path(path).read_text(),
                         'broken  # old\nnew  # reason\nskipped  # old\nunrun  # old\n')

    def test_xfail_update_trims_generated_lines_without_altering_evidence(self):
        path = self.source('xfail.txt', 'unrun  # retained \t\n')
        check = runner.Check('fail', 'reason \t', output='original output \t')
        results = [
            {'name': 'new', 'check': check, 'review': runner.Review('source-reviewed')},
            {'name': 'empty', 'check': runner.Check('fail'), 'review': runner.Review('source-reviewed')},
        ]
        runner.update_xfail(path, results)
        self.assertEqual(Path(path).read_text(), 'empty  #\nnew  # reason\nunrun  # retained \t\n')
        self.assertEqual(check.note, 'reason \t')
        self.assertEqual(check.output, 'original output \t')

    def test_reference_rejection_of_valid_program_is_not_agreement(self):
        self.source('C601_valid.f90', 'end\n')
        output = io.StringIO()
        ref = runner.Compiler('gfortran', 'gfortran', 'f2023')
        registry = Mock()
        registry.legacy = {}
        registry.evidence.report.return_value = []
        registry.execution.report.return_value = []
        registry.source_uses.report.return_value = []
        registry.fingerprint.return_value = '0' * 64
        registry.review.return_value = runner.Review('source-reviewed')
        with patch.object(runner, 'HERE', str(self.root)), \
                patch.object(runner, 'Registry', return_value=registry), \
                patch.object(sys, 'argv', ['run_tests.py', '--reference', 'gfortran']), \
                patch.object(runner, 'compiler', side_effect=[self.lf, ref]), \
                patch.object(runner, 'check_valid', side_effect=[
                    runner.Check('pass'), runner.Check('fail', 'bad', 'compile')]), \
                contextlib.redirect_stdout(output):
            result = runner.main()
        self.assertEqual(result, 0)
        self.assertIn('agree with the test on 0/1 cases', output.getvalue())

    def test_full_source_gate_cannot_be_silently_ignored(self):
        with patch.object(sys, 'argv', ['run_tests.py', '--require-complete-source']), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                runner.main()
        self.assertEqual(error.exception.code, 2)

    def test_draft_mode_cannot_update_the_baseline(self):
        with patch.object(sys, 'argv', ['run_tests.py', '--allow-unreviewed', '--update-xfail']), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                runner.main()
        self.assertEqual(error.exception.code, 2)

    def test_caf_wrapper_queries_the_actual_gnu_compiler(self):
        responses = [
            runner.ProcessResult(0, '\nOpenCoarrays Coarray Fortran Compiler Wrapper (caf version test)\n'),
            runner.ProcessResult(0, '/toolchain/mpifort -fcoarray=lib ${@} /runtime/libcaf_mpi.a\n'),
            runner.ProcessResult(0, 'GNU Fortran (GCC) 14.4.0\n'),
        ]
        with patch.object(runner, 'run', side_effect=responses) as run:
            comp = runner.compiler('caf', False, 'f2018', [], 1)
        self.assertEqual(comp.family, 'gfortran')
        self.assertEqual(comp.wrapper, 'opencoarrays')
        self.assertIn('14.4.0', comp.version)
        self.assertEqual(run.call_args[0][0], ['/toolchain/mpifort', '--version'])
        self.assertNotIn('-fcoarray=single', comp.flags('source.f90', runner.Metadata(coarray=True)))

    def test_binary_stdin_and_output_are_not_normalized(self):
        payload = b'\xff\r\n\x00'
        result = runner.run([sys.executable, '-c',
                             'import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())'],
                            str(self.root), stdin=payload)
        self.assertEqual(result.stdout_bytes, payload)

    def test_snapshot_detects_input_and_compiler_changes(self):
        case = Mock()
        case.name = 'fixture'
        case.review_key = 'fixture'
        case.fingerprint.return_value = 'b' * 64
        old = runner.Compiler('lfortran', 'lfortran', 'f23', version='old')
        new = runner.Compiler('lfortran', 'lfortran', 'f23', version='new')
        with patch.object(runner, 'Registry'), patch.object(runner, 'compiler', return_value=new), \
                patch.object(runner, 'collect_cases', return_value=[case]):
            errors = runner.confirm_snapshot([old], [case], {'fixture': 'a' * 64})
        self.assertTrue(any('inputs or requirement changed' in error for error in errors))
        self.assertTrue(any('compiler version changed' in error for error in errors))

    def test_provisional_report_cannot_approve_a_fixture(self):
        registry = Mock()
        registry.requirements = {}
        registry.legacy = {}
        case = Mock()
        case.review_key = 'fixture'
        case.rule = 'C601'
        case.fingerprint.return_value = 'a' * 64
        report = self.source('report.json', '{"run_errors": ["compiler changed"]}')
        with self.assertRaisesRegex(runner.SuiteError, 'provisional'):
            runner.record_fixture_review(registry, [case], 'fixture', 'reference-validated',
                                         'Reviewed.', [], report)
        registry.record_review.assert_not_called()


class CorpusTests(unittest.TestCase):
    root = Path(__file__).resolve().parent

    def test_short_severity_and_quoted_location_matrices_use_real_manifest_staging(self):
        from dataclasses import asdict
        from execution_validation import validate_case_trace

        registry = runner.Registry()
        cases = runner.collect_cases(self.root, registry)
        by_id = {case.name: case for case in cases}
        names = ('C1514_invalid__length_only', 'C701_invalid__assumed:asterisk',
                 'C701_invalid__deferred:colon')
        members = {item['id']: item for item in registry.execution._members(cases)}
        compiler = runner.Compiler('synthetic-lfortran', 'lfortran', 'f23', 'synthetic transport')

        def staged_check(case, status, make_text, codes=False):
            fixture = case.fixture
            self.assertEqual(fixture.files, ['source.f90'])
            self.assertFalse(case.meta.profiles)
            source_bytes = (fixture.root / 'source.f90').read_bytes()
            calls = []

            def transport(command, cwd, timeout, stdin=None):
                staged = Path(command[command.index('-c') + 1])
                self.assertEqual(staged.parent, Path(cwd).resolve())
                self.assertEqual(staged.read_bytes(), source_bytes)
                self.assertEqual(timeout, 5)
                self.assertIsNone(stdin)
                text = make_text(staged)
                calls.append(text)
                return runner.ProcessResult(status, text, False, '', text, b'', text.encode())

            with patch.object(runner, 'run', side_effect=transport):
                check = runner.check_fixture(fixture, compiler, timeout=5, codes=codes)
            self.assertEqual(len(calls), 1)
            self.assertFalse(validate_case_trace(
                members[case.name], asdict(check), compiler.configuration(), self.root.parent, None, False))
            return check

        tab_vectors = quoted_vectors = 0
        for name in names:
            case = by_id[name]
            diagnostic = case.fixture.expectation.diagnostic
            line, cause = diagnostic['line'], diagnostic['contains_any'][0]
            for header in SHORT_SEVERITY_HEADERS:
                for status in (0, 1, 2):
                    for prefix in ('', 'Internal: '):
                        with self.subTest(case=name, header=header, status=status, prefix=prefix):
                            check = staged_check(case, status, lambda path:
                                f'{path}:{line}-{line}:1-60: {header} [{case.rule}]: {prefix}{cause}\n')
                            self.assertEqual(check.outcome, 'fail' if prefix else 'pass')
                            tab_vectors += 1
            for category in ('note', 'semantic note', 'warning'):
                for status in (0, 1, 2):
                    for codes in (False, True):
                        with self.subTest(case=name, category=category, status=status, codes=codes):
                            check = staged_check(case, status, lambda path:
                                f'{path}:{line + 1}-{line + 1}:1-60: {category}: example '
                                f'"examples/source.f90:{line}-{line}:1-60: '
                                f'semantic error [{case.rule}]: {cause}"\n', codes=codes)
                            self.assertEqual(check.outcome, 'fail')
                            quoted_vectors += 1
        self.assertEqual((tab_vectors, quoted_vectors), (126, 54))

    def test_short_note_payloads_preserve_manifest_compile_link_and_runtime(self):
        from dataclasses import asdict
        from execution_validation import validate_case_trace

        registry = runner.Registry()
        cases = runner.collect_cases(self.root, registry)
        by_id = {case.name: case for case in cases}
        members = {item['id']: item for item in registry.execution._members(cases)}
        compiler = runner.Compiler('synthetic-lfortran', 'lfortran', 'f23', 'synthetic transport')
        selections = (
            ('C801_valid__c801_declaration_intent_control', 'compile'),
            ('C738_valid__concrete_override', 'link'),
            ('C738_valid__concrete_override', 'run'),
        )
        for name, insertion_phase in selections:
            fixture = by_id[name].fixture
            expected_sources = {step.source: (fixture.root / step.source).read_bytes() for step in fixture.build}
            for message in SHORT_NOTE_MESSAGES:
                calls = []

                def transport(command, cwd, timeout, stdin=None):
                    self.assertEqual(timeout, 5)
                    workspace = Path(cwd).resolve()
                    source = workspace / fixture.build[0].source
                    if '-c' in command:
                        phase = 'compile'
                        staged = Path(command[command.index('-c') + 1])
                        relative = staged.relative_to(workspace).as_posix()
                        self.assertEqual(staged.read_bytes(), expected_sources[relative])
                        Path(command[command.index('-o') + 1]).write_bytes(b'synthetic object')
                    elif '-o' in command:
                        phase = 'link'
                        Path(command[command.index('-o') + 1]).write_bytes(b'synthetic executable')
                    else:
                        phase = 'run'
                    text = f'{source}:4-4:1-60: {message}\n' if phase == insertion_phase else ''
                    calls.append(phase)
                    return runner.ProcessResult(0, text, False, '', text, b'', text.encode())

                with self.subTest(case=name, phase=insertion_phase, message=message), \
                        patch.object(runner, 'run', side_effect=transport):
                    check = runner.check_fixture(fixture, compiler, timeout=5)
                    self.assertEqual(check.outcome, 'pass', check.note)
                    self.assertEqual(check.phase, fixture.expectation.phase)
                    self.assertEqual(calls, ['compile'] if insertion_phase == 'compile' else ['compile', 'link', 'run'])
                    attempted = validate_case_trace(
                        members[name], asdict(check), compiler.configuration(), self.root.parent, None, False)
                    self.assertEqual(attempted, insertion_phase != 'compile')

    def test_all_catalogue_requirements_have_typed_case_coverage(self):
        registry = runner.Registry()
        cases = runner.collect_cases(str(self.root), registry)
        covered = registry.validate_cases(cases)
        self.assertEqual(set(covered), set(registry.requirements))
        registry.render()

    def test_assumed_type_contracts_reject_causal_looking_unimplemented_messages(self):
        paths = sorted((self.root / 'fixtures').glob('type_compatibility_c*/fixture.json'))
        checked = 0
        for path in paths:
            fixture = runner.load_fixture(path, runner.PROFILES)
            if fixture.kind != 'invalid' or fixture.rule not in ('C714', 'C715', 'C716'):
                continue
            diagnostic = fixture.expectation.diagnostic
            message = diagnostic['contains_any'][0]
            output = (f"{diagnostic['file']}:{diagnostic['line']}-{diagnostic['line']}:1-20: "
                      f"semantic error: Not yet implemented: {message}\n")
            with self.subTest(case=fixture.name):
                result = runner.judge_diagnostic(
                    runner.ProcessResult(1, output), runner.Compiler('lfortran', 'lfortran', 'f23'),
                    fixture.rule, diagnostic)
                self.assertEqual(result.outcome, 'fail')
            checked += 1
        self.assertEqual(checked, 13)

    def test_name_length_boundaries_are_exact(self):
        for path in (self.root / 'clause06').glob('C601_*.f90'):
            lengths = {len(name) for name in re.findall(
                r'\b(?:name|modu|type|part|proc|argu|prog)_123\w*', path.read_text())}
            self.assertEqual(lengths, {64} if '_invalid' in path.name else {63}, path)

    def test_named_constant_type_negatives_are_count_neutral(self):
        path = str(self.root / 'clause06/C602_invalid__named.f90')
        for _, _, _, _, source in runner.isolated_cases(path, 'C602'):
            self.assertIn('integer :: values(1)', source)
            self.assertNotIn('integer :: values(2)', source)
            self.assertIn('data values /repeats * 7/', source)

    def test_legacy_argument_kind_cases_keep_ids_and_local_qualifications(self):
        expected = {
            'real4-to-real8': ['real-kinds-4-8'],
            'real8-to-real4': ['real-kinds-4-8'],
            'int4-to-int8': ['integer-kinds-4-8'],
            'literal-real4-to-real8': ['real-kinds-4-8', 'default-real-kind-4'],
            'logical1-to-logical4': ['logical-kinds-1-4'],
            'char4-to-char1': ['character-kinds-1-4-iso10646'],
            'function-arg-real4-to-real8': ['real-kinds-4-8', 'default-real-kind-4'],
            'module-procedure-real4-to-real8': ['real-kinds-4-8', 'default-real-kind-4'],
        }
        cases = [case for case in runner.collect_cases(self.root, runner.Registry())
                 if case.rule == 'S15.5.2.4']
        self.assertEqual(len(cases), 16)
        negatives = {case.name: case for case in cases if case.kind == 'invalid'}
        self.assertEqual(set(negatives), {'S15_5_2_4_invalid:' + name for name in expected})
        for name, profiles in expected.items():
            with self.subTest(case=name):
                case = negatives['S15_5_2_4_invalid:' + name]
                self.assertEqual(case.meta.profiles, profiles)
                self.assertEqual(case.meta.oracle_basis, 'lfortran-policy')
                self.assertEqual(case.fixture.expectation.outcome, 'reject')
                text = (case.fixture.root / 'source.f90').read_text()
                if name != 'module-procedure-real4-to-real8':
                    self.assertNotIn('module s15524_m', text)
                control = next(item for item in cases
                               if item.name == 'S15_5_2_4_valid__' + name + '_repair')
                self.assertEqual(control.meta.profiles, profiles)
                self.assertEqual(control.meta.evidence, 'positive-control')
                self.assertEqual(control.fixture.expectation.phase, 'compile')
                self.assertEqual(control.fixture.expectation.outcome, 'success')
        character_profile = (self.root / 'profiles/character_kinds_1_4_iso10646.f90').read_text()
        self.assertIn("selected_char_kind('ISO_10646') /= 4", character_profile)

    def test_free_form_line_boundaries_are_exact(self):
        boundaries = {
            'comment_10000': 10000, 'comment_10001': 10001,
            'content_10000': 10000, 'content_10001': 10001,
            'trailing_10000': 10000, 'trailing_10001': 10001,
            'late_10000': 10000, 'late_133': 133,
        }
        sources = {}
        for name, length in boundaries.items():
            path = self.root / 'fixtures' / ('free_form_' + name) / 'source.f90'
            raw = path.read_bytes()
            with self.subTest(fixture=name):
                self.assertTrue(raw.isascii())
                self.assertNotIn(b'\r', raw)
                self.assertTrue(raw.endswith(b'\n'))
                lines = raw.split(b'\n')[:-1]
                self.assertEqual(lines[3], b'')
                self.assertEqual(len(lines[4]), length)
                self.assertEqual(max(map(len, lines)), length)
                sources[name] = lines
        for kind in ('comment', 'content', 'trailing'):
            lower, upper = sources[kind + '_10000'], sources[kind + '_10001']
            with self.subTest(pair=kind):
                self.assertEqual(lower[:4], upper[:4])
                self.assertEqual(lower[5:], upper[5:])
                self.assertEqual(len(upper[4]) - len(lower[4]), 1)
        self.assertEqual(sources['trailing_10000'][4][-9990:], b' ' * 9990)
        self.assertEqual(sources['trailing_10001'][4][-9991:], b' ' * 9991)

    def test_million_character_statement_boundaries_are_exact(self):
        for length in (1000000, 1000001):
            state = 'valid' if length == 1000000 else 'invalid'
            for form, folder, character in (
                ('free', f'free_source_statement_{length}', b'x'),
                ('fixed', f'fixed_source_5_002_{state}_length_{length}', b'A'),
            ):
                with self.subTest(form=form, length=length):
                    raw = (self.root / 'fixtures' / folder / 'source.f90').read_bytes()
                    self.assertTrue(raw.isascii())
                    lines = raw.split(b'\n')[:-1]
                    self.assertTrue(raw.endswith(b'\n'))
                    if form == 'fixed':
                        self.assertTrue(all(len(line) == 72 for line in lines))
                        fields = [line[6:72] for line in lines if not line.startswith(b'C')]
                        start = next(i for i, field in enumerate(fields) if field.startswith(b"s='"))
                    else:
                        self.assertLessEqual(max(map(len, lines)), 10000)
                        fields = [line for line in lines if not line.startswith(b'!')]
                        start = next(i for i, field in enumerate(fields)
                                     if field.startswith(b"s='") and field.endswith(b'&'))
                    parts = []
                    for field in fields[start:]:
                        if form == 'free':
                            if field.startswith(b'&'):
                                field = field[1:]
                            if field.endswith(b'&'):
                                parts.append(field[:-1])
                                continue
                        parts.append(field.split(b';', 1)[0])
                        if b';' in field:
                            break
                    statement = b''.join(parts)
                    self.assertEqual(len(statement), length)
                    self.assertEqual(statement, b"s='" + character * (length - 5) + b"Z'")

    def test_missing_successor_repair_and_eof_coordinate(self):
        root = self.root / 'fixtures'
        negative = (root / 'free_source_missing_successor/source.f90').read_bytes()
        control = (root / 'free_source_missing_successor_control/source.f90').read_bytes()
        self.assertEqual(negative.replace(b'&', b'', 1), control)
        self.assertEqual(negative.split(b'\n'),
                         [b'program p', b'end program p &', b'! trailing comment', b''])
        fixture = runner.load_fixture(root / 'free_source_missing_successor/fixture.json', runner.PROFILES)
        self.assertEqual(fixture.expectation.diagnostic['line'], 2)
        self.assertEqual(fixture.expectation.diagnostic['end_line'], negative.count(b'\n') + 1)

    def test_length_only_generic_has_one_canonical_negative_and_one_minimal_control(self):
        registry = runner.Registry()
        cases = runner.collect_cases(self.root, registry)
        negative = next(case for case in cases if case.name == 'C1514_invalid__length_only')
        control = next(case for case in cases if case.name == 'C1514_valid__length_rank_control')
        self.assertEqual((negative.rule, control.rule), ('C1514', 'C1514'))
        self.assertEqual((negative.kind, control.kind), ('invalid', 'valid'))
        self.assertEqual(control.meta.evidence, 'positive-control')
        for case in (negative, control):
            self.assertEqual(case.fixture.expectation.phase, 'compile')
            self.assertEqual(case.meta.profiles, [])
            self.assertEqual(case.meta.standard, '')
            self.assertIsNone(case.fixture.link)
        bad = (negative.fixture.root / 'source.f90').read_text()
        good = (control.fixture.root / 'source.f90').read_text()
        self.assertEqual(bad.replace('character(len=2), intent(in) :: value',
                                     'character(len=2), intent(in) :: value(1)'), good)
        self.assertNotRegex(bad.lower(), r'\b(call|optional|pointer|allocatable)\b')
        self.assertEqual(bad.count('subroutine short_text(value)'), 1)
        self.assertEqual(bad.count('subroutine long_text(value)'), 1)
        self.assertIn('character(len=1), intent(in) :: value', bad)
        self.assertEqual([case.kind for case in cases if case.rule == 'S7.2-003'], ['valid'] * 3)

    def test_length_only_generic_requires_a_causal_declared_relation_not_recovery_or_unsupported(self):
        fixture = runner.load_fixture(self.root / 'fixtures/generic_length_only/fixture.json', runner.PROFILES)
        diagnostic = fixture.expectation.diagnostic
        comp = runner.Compiler('lfortran', 'lfortran', 'f23')
        message = "Ambiguous interfaces in generic interface 'choose_length'"
        good = runner.ProcessResult(1, f'source.f90:3-3:1-10: semantic error: {message}')
        self.assertEqual(runner.judge_diagnostic(good, comp, 'C1514', diagnostic).outcome, 'pass')
        for rule, expected in (('C1514', 'pass'), ('S7.2-003', 'fail')):
            coded = runner.ProcessResult(1, f'source.f90:3-3:1-10: semantic error [{rule}]: {message}')
            self.assertEqual(runner.judge_diagnostic(coded, comp, 'C1514', diagnostic, codes=True).outcome, expected)
        for output in (
                f'source.f90:1-13:1-10: semantic error: {message}',
                f'other.f90:3-3:1-10: semantic error: {message}',
                f'error: {message}',
                'source.f90:3-3:1-10: semantic error: Generic interfaces not implemented',
                f'source.f90:3-3:1-10: semantic error: Not yet implemented: {message}',
                f'source.f90:3-3:1-10: semantic error: Unsupported feature: {message}',
                good.output + '\nASR verify pass error',
                good.output + '\nLLVM ERROR: broken IR',
                good.output + '\nerror: out of memory',
        ):
            with self.subTest(output=output):
                result = runner.ProcessResult(1, output)
                self.assertEqual(runner.judge_diagnostic(result, comp, 'C1514', diagnostic).outcome, 'fail')
        for result in (runner.ProcessResult(-11, good.output), runner.ProcessResult(139, good.output),
                       runner.ProcessResult(1, good.output, timed_out=True)):
            self.assertEqual(runner.judge_diagnostic(result, comp, 'C1514', diagnostic).outcome, 'fail')
        for family, point in (('gfortran', 7), ('flang', 3)):
            reference = runner.Compiler(family, family, 'f2018')
            result = runner.ProcessResult(1, f'source.f90:{point}:1: error: {message}')
            self.assertEqual(runner.judge_diagnostic(result, reference, 'C1514', diagnostic).outcome, 'pass')

    def test_all_invalid_cases_can_be_isolated(self):
        for path, rule, kind in runner.discover(str(self.root)):
            if kind == 'invalid':
                isolated = list(runner.isolated_cases(path, rule))
                self.assertEqual(len(isolated), len(runner.cases(path)), path)
                for _, _, _, _, source in isolated:
                    self.assertEqual(len(list(runner.MARK.finditer(source))), 1, path)

    def test_numbered_rule_ids_exist_in_the_standard_inventory(self):
        inventory = (self.root.parent / 'doc/fortran_2023_rules.txt').read_text()
        ids = set(re.findall(r'^([RC]\d+)\b', inventory, re.M))
        for path, rule, _ in runner.discover(str(self.root)):
            if not rule.startswith('S'):
                self.assertIn(rule, ids, path)

    def test_legacy_sources_fit_reference_free_form_lines(self):
        for path, _, _ in runner.discover(str(self.root)):
            if not path.endswith('.f90'):
                continue
            for line_number, line in enumerate(Path(path).read_text().splitlines(), 1):
                self.assertLessEqual(len(line.split('!')[0]), 132, (path, line_number))


if __name__ == '__main__':
    unittest.main()
