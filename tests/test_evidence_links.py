import contextlib
import copy
from dataclasses import asdict, replace
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from fixture_support import load_fixture
from suite_data import Metadata, Registry, SuiteError, write_json


class EvidenceLinkTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.tests = self.root / 'tests'
        self.tests.mkdir()
        self.standard = dict(document='synthetic-pin', edition='F2023', sha256='a' * 64)
        source = dict(self.standard, sections={
            '1.1': dict(sha256='b' * 64, units={'p1': dict(kind='paragraph', sha256='c' * 64)}),
            '1.2': dict(sha256='d' * 64, units={
                'C601': dict(kind='numbered-item', sha256='e' * 64),
                'C602': dict(kind='numbered-item', sha256='f' * 64)}),
        })
        self.index = dict(schema_version=1, standard=self.standard, source_inventory='source.json',
                          rule_inventory='rules.txt', reviews='reviews.json', catalogues=['target.json'],
                          evidence_links='links.json')
        self.target = dict(schema_version=1, section='1.1', review_state='draft', requirements=[
            dict(id='S1.1-001', title='Target', source='1.1 p1', source_units=['p1'],
                 category='effect', diagnostic_obligation='context-dependent',
                 definition='A finite direct effect and a separately linked declaration contrast.',
                 facets=['direct', 'linked'], pending={}, oracle='A source-supported contrast.')],
            accounting=[dict(unit='p1', disposition='requirements', requirements=['S1.1-001'])])
        self.link = dict(
            id='length-link', target=dict(requirement='S1.1-001', facet='linked', source_units=['1.1#p1']),
            basis=['1.2#C601'], claim='Only these two canonical cases.', limitation='Not a runtime effect.',
            cases=[
                dict(id='C601_bad', role='diagnostic', primary_rule='C601', source='1.2#C601',
                     path='tests/bad/fixture.json', phase='compile'),
                dict(id='C601_control', role='positive-control', primary_rule='C601', source='1.2#C601',
                     path='tests/control/fixture.json', phase='compile')])
        write_json(self.root / 'index.json', self.index)
        write_json(self.root / 'source.json', source)
        write_json(self.root / 'target.json', self.target)
        (self.root / 'rules.txt').write_text('C601 test constraint\nC602 other constraint\n')
        self.write_links([self.link])
        (self.tests / 'S1_1_001_valid.f90').write_text(
            '! rule: S1.1-001\n! covers: direct\nprogram direct\nend program direct\n')
        for folder, identifier, outcome, evidence in (
                ('bad', 'C601_bad', 'diagnose', 'effect'),
                ('control', 'C601_control', 'success', 'positive-control')):
            path = self.tests / folder
            path.mkdir()
            (path / 'source.f90').write_text('module example\nend module example\n')
            expect = dict(phase='compile', step='source', outcome=outcome)
            if outcome == 'diagnose':
                expect['diagnostic'] = dict(file='source.f90', line=1, contains_any=['ambiguous'])
            write_json(path / 'fixture.json', dict(
                schema_version=1, id=identifier, rule='C601', facets=[], evidence=evidence,
                files=['source.f90'], build=[
                    dict(id='source', source='source.f90', language='fortran', output='source.o')],
                expect=expect))

    def write_links(self, links):
        write_json(self.root / 'links.json', dict(schema_version=1, standard=self.standard, links=links))

    def change(self, path, modify):
        target = self.root / path
        value = json.loads(target.read_text())
        modify(value)
        write_json(target, value)

    def registry(self):
        return Registry(self.root, 'index.json')

    def cases(self, registry):
        return runner.collect_cases(self.tests, registry)

    def report(self, registry=None, cases=None):
        registry = registry or self.registry()
        return registry.evidence.report(cases or self.cases(registry))[0]

    def approve_prerequisites(self):
        registry = self.registry()
        for section in registry.catalogues:
            registry.record_catalogue_review(section, 'Synthetic independent source review.')
        cases = self.cases(registry)
        for key in sorted({case.review_key for case in cases}):
            runner.record_fixture_review(registry, cases, key, 'source-reviewed',
                                         'Synthetic independent fixture review.', [])
        return registry, cases

    def approve(self):
        registry, cases = self.approve_prerequisites()
        registry.evidence.record_review(cases, 'length-link', 'source-reviewed',
                                        'Synthetic independent semantic connection review.')
        self.assertEqual(self.report(registry, cases)['state'], 'current')
        return registry, cases

    def cli(self, *arguments, checks=None):
        output, errors = io.StringIO(), io.StringIO()
        registry = self.registry()

        def compiler(command, is_target, standard, launcher, timeout):
            return runner.Compiler(command, 'lfortran' if is_target else command,
                                   'f23' if is_target else 'f2018' if command == 'flang' else 'f2023',
                                   version='synthetic', launcher=launcher)

        def execute(case, comp, *args):
            return (checks or {}).get((case.name, comp.command),
                                      runner.Check('pass', phase=case.fixture.expectation.phase
                                                   if case.fixture else 'run'))

        with patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'Registry', return_value=registry), \
                patch.object(runner, 'compiler', side_effect=compiler) as compilers, \
                patch.object(runner, 'execute_case', side_effect=execute) as executions, \
                patch.object(runner, 'confirm_snapshot', return_value=[]), \
                patch.object(sys, 'argv', ['run_tests.py', *arguments]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = runner.main()
        return result, output.getvalue(), errors.getvalue(), compilers.call_count, executions.call_count

    def test_draft_link_is_authored_finite_evidence_not_a_case_or_effect(self):
        registry = self.registry()
        cases = self.cases(registry)
        self.assertEqual(len(cases), 3)
        self.assertEqual(registry.validate_cases(cases), {'S1.1-001': {'direct'}})
        audit = registry.audit(cases)
        self.assertEqual((audit['authored_facets'], audit['linked_facets'],
                          audit['current_linked_facets'], audit['pending_facets'],
                          audit['declared_facets']), (1, 1, 0, 0, 2))
        link = audit['evidence_links'][0]
        self.assertEqual(link['state'], 'draft')
        self.assertEqual(link['review']['state'], 'unreviewed')
        self.assertEqual(link['observation_aggregation'], 'not-computed')
        self.assertEqual({member['primary_rule'] for member in link['cases']}, {'C601'})
        self.assertFalse(audit['complete_source'])

    def test_reviews_bootstrap_source_then_cases_then_link(self):
        registry = self.registry()
        cases = self.cases(registry)
        with self.assertRaisesRegex(SuiteError, 'catalogue source review'):
            registry.evidence.record_review(cases, 'length-link', 'source-reviewed', 'Premature.')
        registry.record_catalogue_review('1.1', 'Synthetic source reviewed first.')
        with self.assertRaisesRegex(SuiteError, 'fixture review is unreviewed'):
            registry.evidence.record_review(cases, 'length-link', 'source-reviewed', 'Still premature.')
        self.approve()
        self.assertEqual(self.report()['state'], 'current')
        self.assertEqual(self.report()['review']['recorded_state'], 'source-reviewed')

    def test_explicit_unreviewed_disputed_and_missing_oracle_states(self):
        registry = self.registry()
        for state in ('unreviewed', 'disputed', 'needs-oracle'):
            with self.subTest(state=state):
                registry.evidence.record_review(self.cases(registry), 'length-link', state, 'Not approved.')
                self.assertEqual(self.report()['state'], state)
        with self.assertRaisesRegex(SuiteError, 'not reference validation'):
            registry.evidence.record_review(self.cases(registry), 'length-link', 'reference-validated', 'No.')
        with self.assertRaisesRegex(SuiteError, 'unknown evidence link'):
            registry.evidence.record_review(self.cases(registry), 'typo', 'source-reviewed', 'No.')

    def test_missing_unknown_duplicate_ids_facets_roles_and_paths_fail(self):
        mutations = [
            ('missing field', lambda link: link.pop('claim')),
            ('empty cases', lambda link: link.update(cases=[])),
            ('missing role', lambda link: link['cases'].pop()),
            ('empty basis', lambda link: link.update(basis=[])),
            ('missing target ID', lambda link: link['target'].pop('requirement')),
            ('unknown target', lambda link: link['target'].update(requirement='S1.1-099')),
            ('unknown facet', lambda link: link['target'].update(facet='unknown')),
            ('duplicate sources', lambda link: link['target'].update(source_units=['1.1#p1', '1.1#p1'])),
            ('unknown source', lambda link: link['basis'].append('1.2#missing')),
            ('unknown case', lambda link: link['cases'][0].update(id='typo')),
            ('wildcard case', lambda link: link['cases'][0].update(id='C601_*')),
            ('duplicate case', lambda link: link['cases'][1].update(id='C601_bad')),
            ('unknown role', lambda link: link['cases'][0].update(role='inferred')),
            ('duplicate role', lambda link: link['cases'][1].update(role='diagnostic')),
            ('duplicate path', lambda link: link['cases'][1].update(path='tests/bad/fixture.json')),
            ('missing path', lambda link: link['cases'][0].update(path='tests/absent/fixture.json')),
            ('wrong path', lambda link: link['cases'][0].update(path='target.json')),
            ('path alias', lambda link: link['cases'][0].update(path='tests/./bad/fixture.json')),
            ('path escape', lambda link: link['cases'][0].update(path='../outside.json')),
            ('absolute path', lambda link: link['cases'][0].update(path=str(self.root / 'target.json'))),
            ('unknown phase', lambda link: link['cases'][0].update(phase='reference')),
            ('wrong phase', lambda link: link['cases'][0].update(phase='run')),
        ]
        for name, modify in mutations:
            with self.subTest(name=name):
                link = copy.deepcopy(self.link)
                modify(link)
                self.write_links([link])
                with self.assertRaises(SuiteError):
                    registry = self.registry()
                    self.cases(registry)

    def test_extra_fields_at_every_link_layer_fail(self):
        for layer in ('registry', 'link', 'target', 'member', 'review'):
            with self.subTest(layer=layer):
                self.write_links([copy.deepcopy(self.link)])
                self.approve()
                def modify(data):
                    link = data['links'][0]
                    obj = {'registry': data, 'link': link, 'target': link['target'],
                           'member': link['cases'][0], 'review': link['review']}[layer]
                    obj['surprise'] = True
                self.change('links.json', modify)
                with self.assertRaisesRegex(SuiteError, 'unknown fields'):
                    self.registry()

    def test_duplicate_link_ids_or_target_facets_fail(self):
        for key in ('id', 'target'):
            with self.subTest(key=key):
                other = copy.deepcopy(self.link)
                if key == 'target':
                    other['id'] = 'another-link'
                self.write_links([self.link, other])
                with self.assertRaisesRegex(SuiteError, 'duplicate link ID or target facet'):
                    self.registry()

    def test_duplicate_json_fields_are_not_silently_discarded(self):
        raw = (self.root / 'links.json').read_text()
        (self.root / 'links.json').write_text(raw.replace(
            '"role": "diagnostic"', '"role": "positive-control", "role": "diagnostic"'))
        with self.assertRaisesRegex(SuiteError, 'duplicate JSON field role'):
            self.registry()

    def test_symlink_aliases_are_not_canonical_case_paths(self):
        (self.root / 'alias.json').symlink_to(self.tests / 'bad/fixture.json')
        self.link['cases'][0]['path'] = 'alias.json'
        self.write_links([self.link])
        with self.assertRaisesRegex(SuiteError, 'noncanonical evidence path'):
            self.registry()

    def test_review_field_types_and_missing_source_basis_fail_clearly(self):
        self.approve()
        original = json.loads((self.root / 'links.json').read_text())
        for update in ({'state': []}, {'fingerprint': None}, {'sources': ['1.1#p1']},
                       {'sources': ['1.1#p1', '1.2#missing']}, {'rationale': ''}):
            with self.subTest(update=update):
                write_json(self.root / 'links.json', original)
                self.change('links.json', lambda data: data['links'][0]['review'].update(update))
                with self.assertRaises(SuiteError):
                    self.registry()

    def test_diagnostic_exclusions_are_strict_opt_in_predicates(self):
        for value in ([], [''], [' '], ['unsupported', 'unsupported'], ['unsupported', None], 'unsupported'):
            with self.subTest(value=value):
                self.change('tests/bad/fixture.json', lambda data: data['expect']['diagnostic'].update(
                    excludes_any=value))
                with self.assertRaises(SuiteError):
                    runner.load_fixture(self.tests / 'bad/fixture.json', set())
        self.change('tests/bad/fixture.json', lambda data: data['expect']['diagnostic'].update(
            excludes_any=['unsupported']))
        fixture = runner.load_fixture(self.tests / 'bad/fixture.json', set())
        comp = runner.Compiler('lfortran', 'lfortran', 'f23')
        output = 'source.f90:1-1:1-10: semantic error: ambiguous\n! unsupported in a source echo only\n'
        result = runner.judge_diagnostic(runner.ProcessResult(1, output), comp, 'C601',
                                        fixture.expectation.diagnostic)
        self.assertEqual(result.outcome, 'pass')

    def test_registry_pin_and_optional_path_are_strict(self):
        for value in ('missing.json', '', None, [], 'tests/../links.json'):
            with self.subTest(path=value):
                self.change('index.json', lambda data: data.update(evidence_links=value))
                with self.assertRaises(SuiteError):
                    self.registry()
        write_json(self.root / 'index.json', self.index)
        self.change('links.json', lambda data: data['standard'].update(sha256='0' * 64))
        with self.assertRaisesRegex(SuiteError, 'pinned standard'):
            self.registry()

    def test_incorrect_primary_source_target_and_policy_relations_fail(self):
        mutations = [
            lambda link: link['target'].update(source_units=['1.2#C601']),
            lambda link: link['target'].update(requirement='C601'),
            lambda link: link['cases'][0].update(primary_rule='S1.1-001'),
            lambda link: link['cases'][0].update(source='1.2#C602'),
            lambda link: link['cases'][0].update(primary_rule='C602', source='1.2#C602'),
            lambda link: link['cases'][0].update(id='length-link'),
            lambda link: link['cases'][0].update(role='positive-control'),
        ]
        for modify in mutations:
            link = copy.deepcopy(self.link)
            modify(link)
            self.write_links([link])
            with self.assertRaises(SuiteError):
                registry = self.registry()
                self.cases(registry)
        self.write_links([self.link])
        self.change('tests/bad/fixture.json', lambda data: data.update(oracle_basis='lfortran-policy'))
        with self.assertRaisesRegex(SuiteError, 'additional diagnostic policy'):
            self.cases(self.registry())

    def test_roles_are_checked_against_real_primary_case_metadata(self):
        self.change('tests/control/fixture.json', lambda data: data.update(evidence='effect'))
        with self.assertRaisesRegex(SuiteError, 'role does not match'):
            self.cases(self.registry())
        self.change('tests/control/fixture.json', lambda data: data.update(evidence='positive-control', rule='C602'))
        with self.assertRaisesRegex(SuiteError, 'primary rule or path'):
            self.cases(self.registry())

    def test_removal_exposes_the_gap_until_pending_is_restored(self):
        self.approve()
        self.write_links([])
        with self.assertRaisesRegex(SuiteError, 'uncovered facets'):
            self.cases(self.registry())
        self.change('target.json', lambda data: data['requirements'][0].update(
            pending={'linked': 'Link removed; authoring is pending again.'}))
        registry = self.registry()
        audit = registry.audit(self.cases(registry))
        self.assertEqual((audit['linked_facets'], audit['pending_facets'], audit['declared_facets']), (0, 1, 2))
        self.assertEqual(audit['catalogue_reviews']['1.1'], 'stale')

    def test_removing_the_registry_path_cannot_improve_completion(self):
        self.change('index.json', lambda data: data.pop('evidence_links'))
        with self.assertRaisesRegex(SuiteError, 'uncovered facets'):
            self.cases(self.registry())

    def test_pending_and_direct_overlap_cannot_double_count_linked_facets(self):
        self.change('target.json', lambda data: data['requirements'][0].update(pending={'linked': 'Still pending.'}))
        with self.assertRaisesRegex(SuiteError, 'declared pending facets'):
            self.cases(self.registry())
        self.change('target.json', lambda data: data['requirements'][0].update(pending={}))
        path = self.tests / 'S1_1_001_valid.f90'
        path.write_text(path.read_text().replace('! covers: direct', '! covers: direct linked'))
        with self.assertRaisesRegex(SuiteError, 'both direct-authored and linked'):
            self.cases(self.registry())

    def test_link_contents_target_and_source_fingerprints_stale_independently(self):
        mutations = [
            ('links.json', lambda data: data['links'][0].update(claim='A changed semantic claim.')),
            ('links.json', lambda data: data['links'][0].update(limitation='A changed finite boundary.')),
            ('target.json', lambda data: data['requirements'][0].update(oracle='A changed oracle.')),
            ('source.json', lambda data: data['sections']['1.1']['units']['p1'].update(sha256='1' * 64)),
            ('source.json', lambda data: data['sections']['1.2']['units']['C601'].update(sha256='2' * 64)),
            ('target.json', lambda data: data.update(review_rationale='A revised source adjudication.')),
        ]
        for filename, modify in mutations:
            with self.subTest(filename=filename):
                self.approve()
                self.change(filename, modify)
                self.assertEqual(self.report()['state'], 'stale')

    def test_renamed_target_cannot_retain_a_link(self):
        self.approve()
        self.change('target.json', lambda data: data['requirements'][0].update(id='S1.1-002'))
        self.change('target.json', lambda data: data['accounting'][0].update(requirements=['S1.1-002']))
        with self.assertRaisesRegex(SuiteError, 'known supplementary requirement'):
            self.registry()

    def test_changed_canonical_inputs_and_execution_set_stale_the_link(self):
        registry, cases = self.approve()
        bad = next(case for case in cases if case.name == 'C601_bad')
        extended = cases + [replace(bad, name='C601_bad:additional')]
        self.assertEqual(self.report(registry, extended)['state'], 'stale')
        source = self.tests / 'bad/source.f90'
        source.write_text(source.read_text() + '! changed bytes\n')
        report = self.report()
        self.assertEqual(report['state'], 'stale')
        self.assertTrue(any('C601_bad: fixture review is stale' in blocker for blocker in report['blockers']))
        self.change('tests/bad/fixture.json', lambda data: data.update(id='C601_renamed'))
        with self.assertRaisesRegex(SuiteError, 'unknown canonical case ID'):
            self.cases(self.registry())

    def test_missing_or_duplicate_canonical_executions_fail(self):
        registry, cases = self.approve()
        with self.assertRaisesRegex(SuiteError, 'unknown canonical case ID'):
            registry.evidence.report([case for case in cases if case.name != 'C601_bad'])
        with self.assertRaisesRegex(SuiteError, 'duplicate execution ID'):
            registry.evidence.report(cases + [cases[0]])

    def test_profile_contents_are_part_of_the_canonical_fingerprint(self):
        profiles = self.tests / 'profiles'
        profiles.mkdir()
        profile = profiles / 'qualified.f90'
        profile.write_text('program profile\nend program profile\n')
        self.change('tests/bad/fixture.json', lambda data: data.update(profiles=['qualified']))
        with patch.object(runner, 'HERE', str(self.tests)), patch.object(runner, 'PROFILES', {'qualified'}):
            self.approve()
            profile.write_text(profile.read_text() + '! changed profile\n')
            self.assertEqual(self.report()['state'], 'stale')

    def test_disputed_unreviewed_and_wrong_source_fixture_reviews_block_links(self):
        for state, sources in (('disputed', ['C601']), ('unreviewed', ['C601']),
                               ('source-reviewed', ['C602'])):
            with self.subTest(state=state, sources=sources):
                registry, cases = self.approve()
                bad = next(case for case in cases if case.name == 'C601_bad')
                registry.record_review(bad.review_key, bad.fingerprint(registry), state, 'Changed adjudication.', sources)
                self.assertEqual(self.report(registry, cases)['state'], 'stale')
                with self.assertRaisesRegex(SuiteError, 'cannot review linked evidence'):
                    registry.evidence.record_review(cases, 'length-link', 'source-reviewed', 'Cannot bypass.')

    def test_reference_approval_must_include_supported_mode_and_actual_phase(self):
        self.change('tests/bad/fixture.json', lambda data: data.update(standard='f2023'))
        for phase, mode in (('run', 'f2023'), ('reference', 'f2023'), ('compile', 'f2018')):
            with self.subTest(phase=phase, mode=mode):
                registry, cases = self.approve_prerequisites()
                bad = next(case for case in cases if case.name == 'C601_bad')
                observation = dict(case=bad.name, compiler='gfortran', version='synthetic',
                                   standard=mode, phase=phase, outcome='pass')
                registry.record_review(bad.review_key, bad.fingerprint(registry), 'reference-validated',
                                       'Legacy permissive record.', ['C601'], [observation])
                with self.assertRaisesRegex(SuiteError, 'required phase and supported mode'):
                    registry.evidence.record_review(cases, 'length-link', 'source-reviewed', 'Not sufficient.')
        registry.record_review(bad.review_key, bad.fingerprint(registry), 'reference-validated',
                               'Correct mode and phase.', ['C601'],
                               [dict(observation, standard='f2023', phase='compile')])
        registry.evidence.record_review(cases, 'length-link', 'source-reviewed', 'Separate semantic review.')
        self.assertEqual(self.report(registry, cases)['state'], 'current')

    def test_reference_reports_cannot_autoapprove_wrong_phase_skips_or_unsupported_modes(self):
        self.change('tests/bad/fixture.json', lambda data: data.update(standard='f2023'))
        registry = self.registry()
        cases = self.cases(registry)
        bad = next(case for case in cases if case.name == 'C601_bad')
        path = self.root / 'observations.json'
        for outcome, phase, mode in (('pass', 'run', 'f2023'), ('pass', 'compile', 'f2018'),
                                     ('fail', 'compile', 'f2023'), ('skip', 'profile-run', 'f2023'),
                                     ('error', 'harness', 'f2023')):
            with self.subTest(outcome=outcome, phase=phase, mode=mode):
                write_json(path, dict(
                    compilers=[dict(command='gfortran', version='synthetic', standard=mode)],
                    results=[dict(name=bad.name, review=dict(fingerprint=bad.fingerprint(registry)),
                                  references={'gfortran': dict(outcome=outcome, phase=phase)})]))
                with self.assertRaisesRegex(SuiteError, 'required phase and supported mode'):
                    runner.record_fixture_review(registry, cases, bad.review_key, 'reference-validated',
                                                 'Cannot infer semantic success.', [], path)
                self.assertNotIn(bad.review_key, registry.reviews)

    def test_case_requirements_and_source_reviews_are_bound(self):
        canonical = dict(schema_version=1, section='1.2', requirements=[
            dict(id='C601', title='Canonical constraint', source='1.2 C601', source_units=['C601'],
                 category='restriction', diagnostic_obligation='required', definition='Original constraint.',
                 facets=['declaration'], pending={}, oracle='A source-defined report.')],
            accounting=[dict(unit=name, disposition='requirements', requirements=[name])
                        for name in ('C601', 'C602')])
        write_json(self.root / 'canonical.json', canonical)
        self.change('index.json', lambda data: data['catalogues'].append('canonical.json'))
        for folder in ('bad', 'control'):
            self.change(f'tests/{folder}/fixture.json', lambda data: data.update(facets=['declaration']))
        self.approve()
        self.change('canonical.json', lambda data: data['requirements'][0].update(definition='Changed constraint.'))
        report = self.report()
        self.assertEqual(report['state'], 'stale')
        self.assertEqual(report['source_reviews']['1.2']['state'], 'stale')
        self.assertEqual({member['review']['state'] for member in report['cases']}, {'stale'})

    def test_unrelated_default_metadata_and_fingerprints_are_unchanged(self):
        self.write_links([])
        self.change('target.json', lambda data: data['requirements'][0].update(pending={'linked': 'Not authored.'}))
        with_registry = self.registry()
        cases = self.cases(with_registry)
        first = {case.name: case.fingerprint(with_registry) for case in cases}
        self.change('index.json', lambda data: data.pop('evidence_links'))
        without_registry = self.registry()
        self.assertEqual(first, {case.name: case.fingerprint(without_registry)
                                 for case in self.cases(without_registry)})
        self.assertEqual(asdict(Metadata()), dict(
            facets=[], evidence='effect', coarray=False, profiles=[], images=1, standard='',
            reference_warnings=[], oracle_basis='standard', oracle_profile=''))
        self.assertEqual(with_registry.definition_material('C601'), {'numbered_rule': 'C601'})

    def test_normal_audit_and_baseline_require_link_review_even_with_approved_cases(self):
        self.approve_prerequisites()
        result, _, _, _, calls = self.cli('--audit')
        self.assertEqual((result, calls), (1, 0))
        self.assertEqual(self.cli('--audit', '--allow-unreviewed')[0], 0)
        result, _, error, compilers, calls = self.cli('--update-xfail', '-t', 'C601')
        self.assertEqual((result, compilers, calls), (2, 0, 0))
        self.assertIn('unreviewed/stale linked evidence', error)
        self.assertFalse((self.tests / 'expected_failures.txt').exists())
        self.assertEqual(self.cli('-t', 'C601')[0], 1)
        self.assertEqual(self.cli('--allow-unreviewed', '-t', 'C601')[0], 0)
        self.approve()
        self.assertEqual(self.cli('--audit')[0], 0)

    def test_full_source_closure_cannot_bypass_draft_or_stale_evidence(self):
        write_json(self.root / 'canonical.json', dict(
            schema_version=1, section='1.2', requirements=[],
            accounting=[dict(unit=name, disposition='requirements', requirements=[name])
                        for name in ('C601', 'C602')]))
        self.change('index.json', lambda data: data['catalogues'].append('canonical.json'))
        self.change('index.json', lambda data: data.update(source_inventory_review=dict(
            state='reviewed', fingerprint=hashlib.sha256((self.root / 'source.json').read_bytes()).hexdigest(),
            rationale='Synthetic complete census.')))
        registry, cases = self.approve_prerequisites()
        audit = registry.audit(cases)
        self.assertEqual(audit['unresolved_base_units'], 0)
        self.assertEqual(audit['sections_without_catalogues'], [])
        self.assertFalse(audit['complete_source'])
        self.assertEqual(self.cli('--audit', '--require-complete-source', '--allow-unreviewed')[0], 1)
        self.approve()
        self.assertTrue(self.registry().audit(self.cases(self.registry()))['complete_source'])
        self.assertEqual(self.cli('--audit', '--require-complete-source')[0], 0)
        self.change('links.json', lambda data: data['links'][0].update(claim='Changed finite claim.'))
        self.assertEqual(self.cli('--audit', '--require-complete-source', '--allow-unreviewed')[0], 1)

    def test_parent_review_cli_is_explicit_and_separate_from_observations(self):
        self.assertEqual(self.cli('--record-catalogue-review', '1.1', '--review-rationale', 'Source review.')[0], 0)
        self.assertEqual(self.cli('--record-evidence-review', 'length-link', '--review-state', 'source-reviewed',
                                  '--review-rationale', 'Premature link review.')[0], 2)
        self.approve_prerequisites()
        result, _, _, compilers, calls = self.cli(
            '--record-evidence-review', 'length-link', '--review-state', 'source-reviewed',
            '--review-rationale', 'Independent relation review, not compiler inference.')
        self.assertEqual((result, compilers, calls), (0, 0, 0))
        self.assertEqual(self.report()['state'], 'current')
        for arguments in (
            ['--record-evidence-review', 'length-link', '--update-xfail'],
            ['--record-evidence-review', 'length-link', '--record-review', 'C601_bad'],
            ['--record-evidence-review', 'length-link', '--review-state', 'reference-validated',
             '--review-rationale', 'Compiler inference.'],
            ['--record-evidence-review', 'length-link', '--review-state', 'source-reviewed',
             '--review-rationale', 'Compiler inference.', '--review-report', 'observations.json'],
        ):
            with self.subTest(arguments=arguments), self.assertRaises(SystemExit):
                self.cli(*arguments)

    def test_reports_coverage_and_filters_do_not_execute_links_or_credit_target_effects(self):
        path = self.root / 'report.json'
        result, output, _, _, calls = self.cli(
            '--allow-unreviewed', '-t', 'C601', '--reference', 'gfortran', '--reference', 'flang',
            '--coverage', str(self.root / 'rules.txt'), '--report', str(path))
        self.assertEqual((result, calls), (0, 6))
        report = json.loads(path.read_text())
        self.assertEqual({row['name'] for row in report['results']}, {'C601_bad', 'C601_control'})
        self.assertEqual({row['rule'] for row in report['results']}, {'C601'})
        self.assertEqual(report['source_audit']['authored_facets'], 1)
        self.assertEqual(report['source_audit']['current_linked_facets'], 0)
        link = report['evidence_links'][0]
        self.assertEqual(link['state'], 'draft')
        self.assertEqual(link['observation_aggregation'], 'not-computed')
        self.assertEqual({member['target_observation']['phase'] for member in link['cases']}, {'compile'})
        self.assertIn('no derived pass/effect count', output)
        self.assertNotIn('S1.1-001             valid', output)
        result, output, _, _, calls = self.cli('--list', '-t', 'S1.1-001')
        self.assertEqual((result, calls), (0, 0))
        self.assertIn('LINK DRAFT length-link', output)
        self.cli('--allow-unreviewed', '-t', 'S1.1-001', '--report', str(path))
        linked = json.loads(path.read_text())['evidence_links'][0]
        self.assertEqual({member['observation_state'] for member in linked['cases']}, {'not-selected'})
        self.assertTrue(all(member['target_observation'] is None for member in linked['cases']))

    def test_reference_only_reports_keep_actual_modes_phases_failures_and_skips(self):
        self.approve()
        path = self.root / 'reference.json'
        checks = {
            ('C601_bad', 'flang'): runner.Check('fail', 'unsupported feature', 'compile'),
            ('C601_control', 'flang'): runner.Check('skip', 'optional property absent', 'profile-run'),
        }
        self.cli('--reference-only', '--reference', 'gfortran', '--reference', 'flang',
                 '-t', 'C601', '--report', str(path), checks=checks)
        link = json.loads(path.read_text())['evidence_links'][0]
        self.assertEqual(link['state'], 'current')
        self.assertEqual(link['observation_aggregation'], 'not-computed')
        self.assertTrue(all(member['target_observation'] is None for member in link['cases']))
        observed = {member['id']: member['reference_observations'] for member in link['cases']}
        self.assertEqual([(item['outcome'], item['phase'], item['standard'])
                          for item in observed['C601_bad']], [('pass', 'compile', 'f2023'), ('fail', 'compile', 'f2018')])
        self.assertEqual(observed['C601_control'][1]['outcome'], 'skip')
        self.assertEqual(observed['C601_control'][1]['phase'], 'profile-run')

    def test_snapshot_detects_link_changes_without_any_selected_primary_input_change(self):
        registry, cases = self.approve()
        selected = [case for case in cases if case.rule == 'S1.1-001']
        fingerprints = {case.review_key: case.fingerprint(registry) for case in cases}
        snapshot = registry.evidence.snapshot(cases)
        self.change('links.json', lambda data: data['links'][0].update(claim='Changed during the run.'))
        with patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'Registry', side_effect=self.registry):
            errors = runner.confirm_snapshot([], selected, fingerprints, evidence_snapshot=snapshot)
        self.assertEqual(errors, ['canonical evidence links, dependencies, or reviews changed during the run'])

    def test_snapshot_detects_link_removal_even_with_pending_restored(self):
        registry, cases = self.approve()
        selected = [case for case in cases if case.rule == 'C601']
        fingerprints = {case.review_key: case.fingerprint(registry) for case in cases}
        snapshot = registry.evidence.snapshot(cases)
        self.write_links([])
        self.change('target.json', lambda data: data['requirements'][0].update(pending={'linked': 'Removed.'}))
        with patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'Registry', side_effect=self.registry):
            errors = runner.confirm_snapshot([], selected, fingerprints, evidence_snapshot=snapshot)
        self.assertEqual(errors, ['canonical evidence links, dependencies, or reviews changed during the run'])

    def reuse(self, pattern, supplementary=True):
        link = copy.deepcopy(self.link)
        link['pattern'] = pattern
        if pattern != 'diagnostic-control':
            link['cases'] = [link['cases'][1]]
            link['cases'][0]['role'] = pattern
        if supplementary:
            self.change('source.json', lambda data: data['sections'].update({
                '1.3': dict(sha256='1' * 64, units={
                    'p1': dict(kind='paragraph', sha256='2' * 64)})}))
            write_json(self.root / 'primary.json', dict(
                schema_version=1, section='1.3', requirements=[
                    dict(id='S1.3-001', title='Canonical prose requirement', source='1.3 p1',
                         source_units=['p1'], category='effect' if pattern == 'runtime-effect' else 'restriction',
                         diagnostic_obligation='not-required' if pattern == 'runtime-effect' else 'required',
                         definition='Independently reviewed original source.', facets=['canonical'], pending={},
                         oracle='A finite independent oracle or a source-minimal diagnostic/control contrast.')],
                accounting=[dict(unit='p1', disposition='requirements', requirements=['S1.3-001'])]))
            self.change('index.json', lambda data: data['catalogues'].append('primary.json'))
            link['basis'] = ['1.3#p1']
        for member in link['cases']:
            if supplementary:
                member.update(id=member['id'].replace('C601', 'S1_3_001'),
                              primary_rule='S1.3-001', source='1.3#p1')
            phase = 'run' if pattern == 'runtime-effect' else 'compile'
            member['phase'] = phase
            def modify(data):
                data.update(id=member['id'], rule=member['primary_rule'], standard='f2023',
                            facets=['canonical'] if supplementary else [])
                if pattern == 'runtime-effect':
                    data.update(evidence='effect',
                                link=dict(objects=['source.o'], output='program'),
                                expect=dict(phase='run', outcome='success', exit_code=0))
            self.change(member['path'], modify)
            if pattern == 'runtime-effect':
                (self.root / member['path']).with_name('source.f90').write_text(
                    'program canonical\nend program canonical\n')
        self.write_links([link])
        return link

    def test_supplementary_diagnostic_pair_retains_its_direct_owner_and_review_gates(self):
        link = self.reuse('diagnostic-control')
        registry = self.registry()
        cases = self.cases(registry)
        self.assertEqual(len(cases), 3)
        self.assertEqual({case.rule for case in cases}, {'S1.1-001', 'S1.3-001'})
        report = self.report(registry, cases)
        self.assertEqual(report['pattern'], 'diagnostic-control')
        self.assertEqual(report['state'], 'draft')
        self.assertEqual({member['primary_rule'] for member in report['cases']}, {'S1.3-001'})
        self.assertEqual({member['source'] for member in report['cases']}, {'1.3#p1'})
        self.assertIn('1.3', report['source_reviews'])
        with self.assertRaisesRegex(SuiteError, 'catalogue source review'):
            registry.evidence.record_review(cases, link['id'], 'source-reviewed', 'Premature.')
        self.approve()
        self.assertEqual(self.report()['state'], 'current')

    def test_supplementary_runtime_reuse_preserves_effect_phase_and_mode(self):
        self.reuse('runtime-effect')
        registry, cases = self.approve()
        member = self.report(registry, cases)['cases'][0]
        self.assertEqual((member['role'], member['kind'], member['evidence'], member['phase']),
                         ('runtime-effect', 'valid', 'effect', 'run'))
        case = next(case for case in cases if case.name == member['id'])
        for phase, mode in (('compile', 'f2023'), ('run', 'f2018')):
            observation = dict(case=case.name, compiler='gfortran', version='synthetic',
                               standard=mode, phase=phase, outcome='pass')
            registry.record_review(case.review_key, case.fingerprint(registry), 'reference-validated',
                                   'Incomplete reference qualification.', ['1.3#p1'], [observation])
            with self.assertRaisesRegex(SuiteError, 'required phase and supported mode'):
                registry.evidence.record_review(cases, 'length-link', 'source-reviewed', 'Cannot bypass.')
        registry.record_review(case.review_key, case.fingerprint(registry), 'reference-validated',
                               'Correct phase and mode.', ['1.3#p1'],
                               [dict(observation, phase='run', standard='f2023')])
        registry.evidence.record_review(cases, 'length-link', 'source-reviewed', 'Separate connection review.')
        self.assertEqual(self.report(registry, cases)['state'], 'current')
        self.assertEqual(self.report(registry, cases)['observation_aggregation'], 'not-computed')
        registry.record_review(case.review_key, case.fingerprint(registry), 'source-reviewed',
                               'Review of the wrong source.', ['1.2#C601'])
        with self.assertRaisesRegex(SuiteError, 'fixture review lacks its canonical source'):
            registry.evidence.record_review(cases, 'length-link', 'source-reviewed', 'Cannot bypass.')

    def test_positive_only_reuse_does_not_promote_control_to_runtime_effect(self):
        link = self.reuse('positive-control')
        registry, cases = self.approve()
        member = self.report(registry, cases)['cases'][0]
        self.assertEqual((member['role'], member['evidence'], member['phase']),
                         ('positive-control', 'positive-control', 'compile'))
        self.assertEqual(len(cases), 3)
        link['pattern'] = 'runtime-effect'
        link['cases'][0]['role'] = 'runtime-effect'
        self.write_links([link])
        with self.assertRaisesRegex(SuiteError, 'role does not match'):
            self.cases(self.registry())

    def marked_control_reuse(self, phase='run', mark_target=True):
        link = self.reuse('positive-control')
        self.change('primary.json', lambda data: data['requirements'][0].update(
            category='effect', diagnostic_obligation='not-required',
            facets=['canonical', 'effect'], positive_control_facets=['canonical'],
            pending={'effect': 'A separate effect case is not authored.'}))
        if mark_target:
            self.change('target.json', lambda data: data['requirements'][0].update(
                positive_control_facets=['linked']))
        self.control_phase(link, phase)
        return link

    def control_phase(self, link, phase):
        member = link['cases'][0]
        member['phase'] = phase
        def modify(data):
            data['expect'] = dict(phase=phase, outcome='success')
            if phase == 'compile':
                data['expect']['step'] = 'source'
                data.pop('link', None)
            else:
                data['link'] = dict(objects=['source.o'], output='program')
                if phase == 'run':
                    data['expect']['exit_code'] = 0
        self.change(member['path'], modify)
        (self.root / member['path']).with_name('source.f90').write_text(
            'program synthetic_control\nend program synthetic_control\n')
        self.write_links([link])

    def test_marked_target_rejects_implicit_and_explicit_diagnostic_pairs(self):
        self.cases(self.registry())
        self.change('target.json', lambda data: data['requirements'][0].update(
            positive_control_facets=['linked']))
        for explicit in (False, True):
            link = copy.deepcopy(self.link)
            if explicit:
                link['pattern'] = 'diagnostic-control'
            self.write_links([link])
            with self.subTest(explicit=explicit), self.assertRaisesRegex(SuiteError, 'explicit positive-control pattern'):
                self.registry()

    def test_marked_target_cannot_promote_a_genuine_runtime_effect_pattern(self):
        self.reuse('runtime-effect')
        registry = self.registry()
        self.cases(registry)
        self.change('target.json', lambda data: data['requirements'][0].update(
            positive_control_facets=['linked']))
        with self.assertRaisesRegex(SuiteError, 'explicit positive-control pattern'):
            self.registry()

    def test_loaded_target_designation_cannot_leave_current_evidence_after_a_rejected_review(self):
        link = self.reuse('runtime-effect')
        registry, cases = self.approve()
        registry.requirements['S1.1-001']['positive_control_facets'] = ['linked']
        registry.record_catalogue_review('1.1', 'Independent synthetic control-facet source review.')
        original = copy.deepcopy(registry.evidence.links[link['id']]['review'])
        for operation in (
                lambda: registry.validate_cases(cases),
                lambda: registry.evidence.validate_cases(cases),
                lambda: registry.evidence.report(cases),
                lambda: registry.evidence.snapshot(cases),
                lambda: registry.evidence.record_review(cases, link['id'], 'source-reviewed', 'Cannot promote.')):
            with self.subTest(operation=operation), self.assertRaisesRegex(SuiteError, 'explicit positive-control pattern'):
                operation()
            self.assertEqual(registry.evidence.links[link['id']]['review'], original)

    def test_marked_control_links_preserve_compile_link_run_and_review_prerequisites(self):
        link = self.marked_control_reuse(phase='compile')
        registry = self.registry()
        cases = self.cases(registry)
        self.assertFalse(registry.reviews)
        with self.assertRaisesRegex(SuiteError, 'catalogue source review'):
            registry.evidence.record_review(cases, link['id'], 'source-reviewed', 'Premature.')
        for section in registry.catalogues:
            registry.record_catalogue_review(section, 'Independent synthetic source review only.')
        with self.assertRaisesRegex(SuiteError, 'fixture review is unreviewed'):
            registry.evidence.record_review(cases, link['id'], 'source-reviewed', 'Still premature.')
        for phase in ('compile', 'link', 'run'):
            with self.subTest(phase=phase):
                self.control_phase(link, phase)
                registry, cases = self.approve()
                report = self.report(registry, cases)
                member = report['cases'][0]
                self.assertEqual(report['pattern'], 'positive-control')
                self.assertEqual((member['role'], member['evidence'], member['phase'], member['kind']),
                                 ('positive-control', 'positive-control', phase, 'valid'))
                self.assertEqual(report['state'], 'current')
                self.assertEqual(report['observation_aggregation'], 'not-computed')
                self.assertEqual(len(cases), 3)
                self.assertEqual(registry.requirements['S1.3-001']['pending'],
                                 {'effect': 'A separate effect case is not authored.'})
                wrong = copy.deepcopy(link)
                wrong['cases'][0]['phase'] = 'compile' if phase != 'compile' else 'run'
                self.write_links([wrong])
                with self.assertRaisesRegex(SuiteError, 'declared phase does not match'):
                    self.cases(self.registry())
                self.write_links([link])

    def test_marked_source_controls_cannot_be_promoted_or_mix_roles_through_links(self):
        link = self.marked_control_reuse(mark_target=False)
        registry = self.registry()
        cases = self.cases(registry)
        control = next(case for case in cases if case.name == link['cases'][0]['id'])
        promoted = copy.deepcopy(link)
        promoted['pattern'] = 'runtime-effect'
        promoted['cases'][0]['role'] = 'runtime-effect'
        self.write_links([promoted])
        with self.assertRaisesRegex(SuiteError, 'role does not match'):
            self.cases(self.registry())
        registry = self.registry()
        for evidence, facets, kind, error in (
                ('effect', ['canonical'], 'valid', 'requires positive-control evidence'),
                ('positive-control', ['canonical', 'effect'], 'valid', 'incompatible evidence roles'),
                ('effect', ['canonical'], 'invalid', 'invalid cases cannot cover positive-control')):
            metadata = copy.deepcopy(control.meta)
            metadata.evidence, metadata.facets = evidence, facets
            changed = replace(control, meta=metadata, kind=kind)
            replaced = [changed if case.name == control.name else case for case in cases]
            with self.subTest(evidence=evidence, facets=facets, kind=kind):
                with self.assertRaisesRegex(SuiteError, error):
                    registry.evidence.validate_cases(replaced)
        self.write_links([link])
        registry = self.registry()
        mixed = replace(control, meta=Metadata(facets=['canonical', 'effect'], evidence='positive-control'))
        with self.assertRaisesRegex(SuiteError, 'incompatible evidence roles'):
            registry.evidence.validate_cases([mixed if case.name == control.name else case for case in cases])
        self.cases(registry)

    def test_marked_source_control_keeps_its_role_in_an_unmarked_target_diagnostic_pair(self):
        self.reuse('diagnostic-control')
        self.change('primary.json', lambda data: data['requirements'][0].update(
            category='effect', facets=['violation', 'control'], positive_control_facets=['control']))
        self.change('tests/bad/fixture.json', lambda data: data.update(facets=['violation']))
        self.change('tests/control/fixture.json', lambda data: data.update(facets=['control']))
        registry, cases = self.approve()
        report = self.report(registry, cases)
        self.assertEqual(report['pattern'], 'diagnostic-control')
        self.assertEqual(report['state'], 'current')
        self.assertEqual([(member['role'], member['evidence'], member['phase']) for member in report['cases']],
                         [('diagnostic', 'effect', 'compile'), ('positive-control', 'positive-control', 'compile')])
        self.assertNotIn('positive_control_facets', registry.requirements['S1.1-001'])

    def assert_source_requirement_rejected(self, registry, cases, error):
        original = {name: copy.deepcopy(link.get('review')) for name, link in registry.evidence.links.items()}
        disk = registry.evidence.path.read_bytes()
        name = next(iter(registry.evidence.links))
        for label, operation in (
                ('direct', lambda: registry.validate_cases(cases)),
                ('canonical', lambda: registry.evidence.validate_cases(cases)),
                ('report', lambda: registry.evidence.report(cases)),
                ('snapshot', lambda: registry.evidence.snapshot(cases)),
                ('review', lambda: registry.evidence.record_review(
                    cases, name, 'source-reviewed', 'Incompatible source must not become current.'))):
            with self.subTest(operation=label), self.assertRaisesRegex(SuiteError, error):
                operation()
            self.assertEqual({key: link.get('review') for key, link in registry.evidence.links.items()}, original)
            self.assertEqual(registry.evidence.path.read_bytes(), disk)

    def test_moved_and_removed_source_controls_reject_loaded_and_reloaded_graph_operations(self):
        link = self.marked_control_reuse()
        registry, cases = self.approve()
        source = next(case for case in cases if case.name == link['cases'][0]['id'])
        seed = {path: (self.root / path).read_bytes() for path in ('primary.json', 'reviews.json', 'links.json')}
        original_inputs = source.fixture.inputs()
        original_metadata = copy.deepcopy(source.meta)
        original_phase = source.fixture.expectation.phase
        for mutation in ('move', 'remove'):
            for path, raw in seed.items():
                (self.root / path).write_bytes(raw)
            loaded = self.registry()
            requirement = loaded.requirements[source.rule]
            if mutation == 'move':
                requirement['positive_control_facets'] = ['effect']
            else:
                requirement.pop('positive_control_facets')
            loaded.record_catalogue_review('1.3', 'Independent synthetic changed source designation.')
            loaded.record_review(source.review_key, source.fingerprint(loaded), 'source-reviewed',
                                 'Synthetic refreshed fingerprint cannot bypass the required role.', ['1.3#p1'])
            for mode, current in (('loaded', loaded), ('reloaded', self.registry())):
                with self.subTest(mutation=mutation, mode=mode):
                    self.assertEqual(current.catalogue_review_state('1.3'), 'reviewed')
                    self.assertEqual(current.review(source.review_key, source.fingerprint(current)).state, 'source-reviewed')
                    self.assertEqual(source.fixture.inputs(), original_inputs)
                    self.assertEqual(source.meta, original_metadata)
                    self.assertEqual(source.fixture.expectation.phase, original_phase)
                    self.assert_source_requirement_rejected(current, cases, 'requires effect evidence')
                    with self.assertRaisesRegex(SuiteError, 'requires effect evidence'):
                        self.cases(current)

    def test_canonical_source_facet_and_role_validation_has_direct_case_parity(self):
        link = self.marked_control_reuse()
        registry, cases = self.approve()
        source = next(case for case in cases if case.name == link['cases'][0]['id'])
        for facets, evidence, error in (
                ([], 'positive-control', 'missing, duplicate, or unknown catalogue facets'),
                (['canonical', 'canonical'], 'positive-control', 'missing, duplicate, or unknown catalogue facets'),
                (['missing'], 'positive-control', 'missing, duplicate, or unknown catalogue facets'),
                (['canonical', 'missing'], 'positive-control', 'missing, duplicate, or unknown catalogue facets'),
                (['canonical', 'effect'], 'positive-control', 'incompatible evidence roles'),
                (['effect', 'canonical'], 'effect', 'incompatible evidence roles'),
                (['canonical'], 'effect', 'requires positive-control evidence'),
                (['canonical'], 'context-only', 'requires positive-control evidence'),
                (['effect'], 'positive-control', 'requires effect evidence')):
            metadata = copy.deepcopy(source.meta)
            metadata.facets, metadata.evidence = facets, evidence
            changed = replace(source, meta=metadata)
            current_cases = [changed if case.name == source.name else case for case in cases]
            with self.subTest(facets=facets, evidence=evidence):
                self.assert_source_requirement_rejected(registry, current_cases, error)

    def test_invalid_marked_source_controls_and_policy_do_not_reach_graph_reviews(self):
        link = self.marked_control_reuse(phase='compile')
        registry, cases = self.approve()
        source = next(case for case in cases if case.name == link['cases'][0]['id'])
        original = json.loads(source.fixture.path.read_text())
        for basis in ('standard', 'lfortran-policy'):
            data = copy.deepcopy(original)
            data.update(evidence='effect', oracle_basis=basis,
                        expect=dict(phase='compile', step='source', outcome='diagnose',
                                    diagnostic=dict(file='source.f90', line=1, contains_any=['synthetic'])))
            write_json(source.fixture.path, data)
            fixture = load_fixture(source.fixture.path, runner.PROFILES)
            changed = runner.SuiteCase(fixture.name, fixture.rule, fixture.kind, str(fixture.path),
                                       fixture.meta, fixture.name, fixture=fixture)
            current_cases = [changed if case.name == source.name else case for case in cases]
            for mode, current in (('loaded', registry), ('reloaded', self.registry())):
                with self.subTest(basis=basis, mode=mode):
                    self.assertEqual(changed.kind, 'invalid')
                    self.assert_source_requirement_rejected(
                        current, current_cases, 'invalid cases cannot cover positive-control facets')

    def test_marked_run_control_reference_qualification_does_not_change_its_role(self):
        link = self.marked_control_reuse()
        registry, cases = self.approve()
        control = next(case for case in cases if case.name == link['cases'][0]['id'])
        for phase, mode in (('compile', 'f2023'), ('run', 'f2018')):
            observation = dict(case=control.name, compiler='gfortran', version='synthetic',
                               standard=mode, phase=phase, outcome='pass')
            registry.record_review(control.review_key, control.fingerprint(registry), 'reference-validated',
                                   'Synthetic but unqualified phase/mode.', ['1.3#p1'], [observation])
            with self.assertRaisesRegex(SuiteError, 'required phase and supported mode'):
                registry.evidence.record_review(cases, link['id'], 'source-reviewed', 'Cannot bypass.')
        registry.record_review(control.review_key, control.fingerprint(registry), 'reference-validated',
                               'Synthetic correctly shaped reference.', ['1.3#p1'],
                               [dict(observation, standard='f2023', phase='run')])
        registry.evidence.record_review(cases, link['id'], 'source-reviewed', 'Independent synthetic connection review.')
        report = self.report(registry, cases)
        self.assertEqual(report['state'], 'current')
        self.assertEqual(report['cases'][0]['role'], 'positive-control')
        self.assertEqual(report['cases'][0]['evidence'], 'positive-control')
        self.assertEqual(report['observation_aggregation'], 'not-computed')

    def test_adding_a_target_control_designation_stales_source_case_and_link_material(self):
        self.reuse('positive-control')
        registry, cases = self.approve()
        before = self.report(registry, cases)
        direct = next(case for case in cases if case.rule == 'S1.1-001')
        fingerprint = direct.fingerprint(registry)
        self.change('target.json', lambda data: data['requirements'][0].update(
            positive_control_facets=['linked']))
        registry = self.registry()
        cases = self.cases(registry)
        report = self.report(registry, cases)
        self.assertEqual(report['state'], 'stale')
        self.assertEqual(report['source_reviews']['1.1']['state'], 'stale')
        self.assertNotEqual(report['review']['fingerprint'], before['review']['fingerprint'])
        self.assertNotEqual(direct.fingerprint(registry), fingerprint)
        self.assertEqual(registry.review(direct.review_key, direct.fingerprint(registry)).state, 'stale')
        self.assertEqual(report['cases'][0]['role'], 'positive-control')
        self.assertEqual(report['cases'][0]['review']['state'], before['cases'][0]['review']['state'])

    def test_adding_and_changing_source_control_designations_stales_existing_canonical_evidence(self):
        link = self.reuse('runtime-effect')
        self.change('primary.json', lambda data: data['requirements'][0].update(
            facets=['canonical', 'control', 'other-control'],
            pending={'control': 'Not authored.', 'other-control': 'Not authored.'}))
        for controls in (['control'], ['control', 'other-control']):
            registry, cases = self.approve()
            before = self.report(registry, cases)
            canonical = next(case for case in cases if case.name == link['cases'][0]['id'])
            fingerprint = canonical.fingerprint(registry)
            original_inputs = canonical.fixture.inputs()
            self.change('primary.json', lambda data: data['requirements'][0].update(
                positive_control_facets=controls))
            registry = self.registry()
            report = self.report(registry, self.cases(registry))
            self.assertEqual(canonical.fixture.inputs(), original_inputs)
            self.assertNotEqual(canonical.fingerprint(registry), fingerprint)
            self.assertEqual(report['state'], 'stale')
            self.assertEqual(report['source_reviews']['1.3']['state'], 'stale')
            self.assertEqual(report['cases'][0]['review']['state'], 'stale')
            self.assertNotEqual(report['review']['fingerprint'], before['review']['fingerprint'])
            self.assertEqual(report['cases'][0]['role'], 'runtime-effect')

    def test_numbered_runtime_can_be_reused_without_changing_primary_ownership(self):
        self.reuse('runtime-effect', supplementary=False)
        registry, cases = self.approve()
        member = self.report(registry, cases)['cases'][0]
        self.assertEqual((member['primary_rule'], member['source'], member['phase']),
                         ('C601', '1.2#C601', 'run'))
        self.assertEqual(len(cases), 3)

    def test_supplementary_reuse_requires_explicit_pattern_and_its_own_source(self):
        original = self.reuse('diagnostic-control')
        for modify in (
            lambda link: link.pop('pattern'),
            lambda link: link.update(pattern=None),
            lambda link: link.update(pattern=[]),
            lambda link: link.update(pattern='aggregate'),
            lambda link: link['cases'][0].update(primary_rule='S1.3-099'),
            lambda link: link['cases'][0].update(source='1.1#p1'),
            lambda link: link['cases'][0].update(source='1.2#C601'),
            lambda link: link['cases'][0].update(id='length-link'),
            lambda link: link['target'].update(requirement='S1.3-001', facet='canonical',
                                               source_units=['1.3#p1']),
        ):
            with self.subTest(modify=modify):
                link = copy.deepcopy(original)
                modify(link)
                self.write_links([link])
                with self.assertRaises(SuiteError):
                    self.cases(self.registry())

    def test_singleton_patterns_require_exact_role_count_and_original_case_policy(self):
        original = self.reuse('runtime-effect')
        for modify in (
            lambda link: link.update(cases=[]),
            lambda link: link['cases'].append(copy.deepcopy(link['cases'][0])),
            lambda link: link['cases'][0].update(role='positive-control'),
            lambda link: link.update(pattern='positive-control'),
            lambda link: link['cases'][0].update(phase='compile'),
        ):
            with self.subTest(modify=modify):
                link = copy.deepcopy(original)
                modify(link)
                self.write_links([link])
                with self.assertRaises(SuiteError):
                    self.cases(self.registry())
        self.write_links([original])
        self.change(original['cases'][0]['path'], lambda data: data.update(oracle_basis='lfortran-policy'))
        with self.assertRaisesRegex(SuiteError, 'additional diagnostic policy'):
            self.cases(self.registry())

    def test_supplementary_owner_definition_and_review_stale_reused_evidence(self):
        self.reuse('runtime-effect')
        self.approve()
        self.change('primary.json', lambda data: data['requirements'][0].update(definition='Changed source meaning.'))
        report = self.report()
        self.assertEqual(report['state'], 'stale')
        self.assertEqual(report['source_reviews']['1.3']['state'], 'stale')
        self.assertEqual(report['cases'][0]['review']['state'], 'stale')

    def test_multiple_links_reuse_one_runtime_without_execution_fanout_or_aggregation(self):
        link = self.reuse('runtime-effect')
        other = copy.deepcopy(link)
        other['id'] = 'second-link'
        other['target']['facet'] = 'linked-again'
        self.change('target.json', lambda data: data['requirements'][0]['facets'].append('linked-again'))
        self.write_links([link, other])
        path = self.root / 'reuse-report.json'
        result, output, _, _, calls = self.cli(
            '--allow-unreviewed', '-t', link['cases'][0]['id'], '--reference', 'gfortran',
            '--reference', 'flang', '--report', str(path))
        self.assertEqual((result, calls), (0, 3))
        report = json.loads(path.read_text())
        self.assertEqual(len(report['results']), 1)
        self.assertEqual(report['results'][0]['rule'], 'S1.3-001')
        self.assertEqual(report['results'][0]['check']['phase'], 'run')
        self.assertEqual(report['source_audit']['linked_facets'], 2)
        self.assertEqual(report['source_audit']['current_linked_facets'], 0)
        self.assertEqual(len(report['evidence_links']), 2)
        for item in report['evidence_links']:
            self.assertEqual(item['pattern'], 'runtime-effect')
            self.assertEqual(item['observation_aggregation'], 'not-computed')
            self.assertEqual(item['cases'][0]['target_observation']['phase'], 'run')
            self.assertEqual([obs['standard'] for obs in item['cases'][0]['reference_observations']],
                             ['f2023', 'f2018'])
        self.assertIn('no derived pass/effect count', output)
        result, _, _, _, calls = self.cli('--allow-unreviewed', '-t', 'S1.1-001', '--report', str(path))
        self.assertEqual((result, calls), (0, 1))
        self.assertTrue(all(item['cases'][0]['observation_state'] == 'not-selected'
                            for item in json.loads(path.read_text())['evidence_links']))


if __name__ == '__main__':
    unittest.main()
