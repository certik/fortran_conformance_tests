import contextlib
import collections
import io
from pathlib import Path
import re
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import run_tests as runner


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

    def test_diagnostic_range_can_cover_the_marked_line(self):
        result = runner.ProcessResult(1, 'case.f90:1-3:1-20: syntax error [C801]: repeated')
        self.assertEqual(self.invalid(result, True).outcome, 'pass')

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

    def test_reference_rejection_of_valid_program_is_not_agreement(self):
        self.source('C601_valid.f90', 'end\n')
        output = io.StringIO()
        ref = runner.Compiler('gfortran', 'gfortran', 'f2023')
        registry = Mock()
        registry.legacy = {}
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
        case.review_key = 'fixture'
        case.fingerprint.return_value = 'b' * 64
        old = runner.Compiler('lfortran', 'lfortran', 'f23', version='old')
        new = runner.Compiler('lfortran', 'lfortran', 'f23', version='new')
        with patch.object(runner, 'Registry'), patch.object(runner, 'compiler', return_value=new):
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

    def test_all_catalogue_requirements_have_typed_case_coverage(self):
        registry = runner.Registry()
        cases = runner.collect_cases(str(self.root), registry)
        covered = registry.validate_cases(cases)
        self.assertEqual(set(covered), set(registry.requirements))
        registry.render()

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
