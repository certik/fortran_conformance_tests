import contextlib
import copy
from dataclasses import asdict
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from execution_aggregates import observations
from execution_commands import command_plan, execution_context
from suite_data import Registry, SuiteError, write_json


class ExecutionAggregateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.tests = self.root / 'tests'
        self.tests.mkdir()
        self.standard = dict(document='synthetic-pin', edition='F2023', sha256='a' * 64)
        source = dict(self.standard, sections={
            '1.1': dict(units={'p1': dict(kind='paragraph', sha256='b' * 64)}),
            '1.2': dict(units={
                'p1': dict(kind='paragraph', sha256='c' * 64),
                'p2': dict(kind='paragraph', sha256='d' * 64),
                'C601': dict(kind='numbered-item', sha256='e' * 64)})})
        target = dict(
            schema_version=1, section='1.1', requirements=[
                dict(id='S1.1-001', title='Whole suite', source='1.1 p1', source_units=['p1'],
                     category='effect', diagnostic_obligation='not-required',
                     definition='Synthetic universal obligation.', facets=['whole'],
                     pending={'whole': 'Global source and qualification evidence remains incomplete.'},
                     oracle_limitation='Finite observations are not completion.')],
            accounting=[dict(unit='p1', disposition='requirements', requirements=['S1.1-001'])])
        direct = dict(
            schema_version=1, section='1.2', requirements=[
                dict(id='S1.2-001', title='Effect', source='1.2 p1', source_units=['p1'],
                     category='effect', diagnostic_obligation='not-required',
                     definition='Synthetic direct effect.', facets=['effect'], pending={}, oracle='A run.'),
                dict(id='S1.2-002', title='Context', source='1.2 p2', source_units=['p2'],
                     category='undefined-result', diagnostic_obligation='not-required',
                     definition='Synthetic undefined result.', facets=['context'], pending={},
                     oracle_limitation='Never read the undefined value.')],
            accounting=[
                dict(unit='p1', disposition='requirements', requirements=['S1.2-001']),
                dict(unit='p2', disposition='requirements', requirements=['S1.2-002']),
                dict(unit='C601', disposition='requirements', requirements=['C601'])])
        index = dict(schema_version=1, standard=self.standard, source_inventory='source.json',
                     rule_inventory='rules.txt', reviews='reviews.json',
                     catalogues=['target.json', 'direct.json'], execution_aggregates='aggregates.json')
        self.aggregate = dict(
            id='whole-suite', target=dict(requirement='S1.1-001', facet='whole', source_units=['1.1#p1']),
            basis=['1.1#p1'], scope='all-collected-cases', coverage_credit='none',
            claim='Exactly the current collected suite.', limitation='Neither closure nor universal proof.')
        for name, data in (('index.json', index), ('source.json', source),
                           ('target.json', target), ('direct.json', direct)):
            write_json(self.root / name, data)
        self.write_aggregates([self.aggregate])
        (self.root / 'rules.txt').write_text('C601 synthetic constraint\n')
        for name, header in (
                ('S1_2_001_valid', '! rule: S1.2-001\n! covers: effect\n'),
                ('S1_2_002_valid', '! rule: S1.2-002\n! covers: context\n! evidence: context-only\n'),
                ('C601_valid__run_control', '! rule: C601\n! evidence: positive-control\n')):
            (self.tests / (name + '.f90')).write_text(header + 'program p\nend program\n')
        for folder, identifier, outcome in (('bad', 'C601_bad', 'diagnose'),
                                             ('control', 'C601_control', 'success')):
            path = self.tests / folder
            path.mkdir()
            (path / 'source.f90').write_text('program p\nend program\n')
            expect = dict(phase='compile', step='source', outcome=outcome)
            if outcome == 'diagnose':
                expect['diagnostic'] = dict(file='source.f90', line=1, contains_any=['synthetic'])
            write_json(path / 'fixture.json', dict(
                schema_version=1, id=identifier, rule='C601', facets=[],
                evidence='effect' if outcome == 'diagnose' else 'positive-control',
                files=['source.f90'], build=[
                    dict(id='source', source='source.f90', language='fortran', output='source.o')],
                expect=expect))

    def write_aggregates(self, values):
        write_json(self.root / 'aggregates.json',
                   dict(schema_version=1, standard=self.standard, aggregates=values))

    def change(self, path, modify):
        filename = self.root / path
        value = json.loads(filename.read_text())
        modify(value)
        write_json(filename, value)

    def registry(self):
        return Registry(self.root, 'index.json')

    def cases(self, registry):
        return runner.collect_cases(self.tests, registry)

    def approve_prerequisites(self):
        registry = self.registry()
        for section in registry.catalogues:
            registry.record_catalogue_review(section, 'Synthetic source review.')
        cases = self.cases(registry)
        for key in sorted({case.review_key for case in cases}):
            runner.record_fixture_review(registry, cases, key, 'source-reviewed',
                                         'Synthetic independent fixture review.', [])
        return registry, cases

    def approve(self):
        registry, cases = self.approve_prerequisites()
        registry.execution.record_review(cases, 'whole-suite', 'source-reviewed',
                                         'Synthetic independent whole-inventory review.')
        return registry, cases

    def report(self, registry=None, cases=None):
        registry = registry or self.registry()
        return registry.execution.report(cases or self.cases(registry))[0]

    def identity(self, family='lfortran', standard=None):
        return dict(command=family, family=family, version='fixed-version',
                    standard=standard or ('f23' if family == 'lfortran' else 'f2023'),
                    launcher=[], wrapper='', c_binding_header={})

    def step(self, phase, status=0):
        return dict(phase=phase, step=phase, command=['synthetic-command'],
                    returncode=status, timed_out=False)

    def check(self, member, outcome='pass', identity=None, companion=None):
        identity = identity or self.identity()
        companion = companion or dict(command='cc', version='fixed-companion')
        phase = member['expected_phase']
        workspace = self.root / 'private-runs' / member['id']
        resources = ({'ISO_Fortran_binding.h': str(
            workspace / 'processor-header-test/ISO_Fortran_binding.h')}
            if member['binding_header_required'] else {})
        context = execution_context(workspace, resources)
        plan = command_plan(member, identity, self.root, context, companion)
        trace = [dict(step, returncode=0, timed_out=False) for step in plan]
        trace[-1]['returncode'] = (1 if member['kind'] == 'invalid' else
                                  member['expected_exit'] if phase == 'run' else 0)
        hashes = copy.deepcopy(member['input_hashes'])
        headers = {}
        if resources:
            header = identity.get('c_binding_header') or dict(
                path='/synthetic/ISO_Fortran_binding.h', sha256='f' * 64,
                discovery='synthetic processor query')
            headers['ISO_Fortran_binding.h'] = header
            hashes['@compiler/ISO_Fortran_binding.h'] = header['sha256']
        profiles = {}
        for name, profile_hashes in member['profile_hashes'].items():
            profile_context = execution_context(self.root / 'profile-runs' / name)
            profile_plan = command_plan(None, identity, self.root, profile_context, profile=name)
            profiles[name] = asdict(runner.Check(
                'pass', phase='profile', input_hashes=profile_hashes,
                trace=[dict(step, returncode=0, timed_out=False) for step in profile_plan],
                execution_context=profile_context))
            profiles[name].pop('profile_checks')
        return asdict(runner.Check(outcome, phase=phase, trace=trace, input_hashes=hashes,
                                   profile_checks=profiles, compiler_headers=headers,
                                   execution_context=context))

    def results(self, aggregate, references=(), identities=None):
        identities = identities or {}
        return [
            dict(name=member['id'], rule=member['primary_rule'], kind=member['kind'],
                 check=self.check(member), metadata=copy.deepcopy(member['metadata']),
                 review=copy.deepcopy(member['review']), review_key=member['review_key'],
                 references={name: self.check(member, identity=identities.get(name, self.identity(name)))
                             for name in references}, status='PASS')
            for member in aggregate['members']]

    def project(self, aggregate, results, identities=None, reference_only=False, **kwargs):
        return observations([aggregate], results, identities or [self.identity()],
                            reference_only, source_root=self.root, **kwargs)[0]

    def test_inventory_does_not_create_cases_or_close_the_pending_facet(self):
        registry, cases = self.approve()
        audit = registry.audit(cases)
        self.assertEqual(len(cases), 5)
        self.assertEqual(audit['authored_facets'], 2)
        self.assertEqual(audit['pending_facets'], 1)
        self.assertEqual(audit['linked_facets'], 0)
        self.assertEqual(audit['observational_aggregates'], 1)
        self.assertEqual(audit['current_observational_aggregates'], 1)
        self.assertFalse(audit['complete_source'])
        aggregate = self.report(registry, cases)
        self.assertEqual(aggregate['coverage_credit'], 'none')
        self.assertEqual(aggregate['facet_completion'], 'pending')
        self.assertEqual(aggregate['source_context']['inventory_review_state'], 'unreviewed')
        self.assertEqual(aggregate['cohort_counts'],
                         {'diagnostic-only': 1, 'positive-control': 2, 'runtime-effect': 1, 'context-only': 1})
        self.change('target.json', lambda data: data['requirements'][0].update(pending={}))
        with self.assertRaisesRegex(SuiteError, 'cannot clear.*pending facet'):
            self.registry()

    def test_source_then_fixture_then_inventory_review_is_required(self):
        registry = self.registry()
        with self.assertRaisesRegex(SuiteError, 'catalogue source review'):
            registry.execution.record_review(self.cases(registry), 'whole-suite', 'source-reviewed', 'Too soon.')
        for section in registry.catalogues:
            registry.record_catalogue_review(section, 'Synthetic source review.')
        with self.assertRaisesRegex(SuiteError, 'fixture review is unreviewed'):
            registry.execution.record_review(self.cases(registry), 'whole-suite', 'source-reviewed', 'Too soon.')
        registry, cases = self.approve()
        self.assertEqual(self.report(registry, cases)['state'], 'current')
        with self.assertRaisesRegex(SuiteError, 'not reference validation'):
            registry.execution.record_review(cases, 'whole-suite', 'reference-validated', 'No compiler proof.')

    def test_inventory_adjudication_preserves_explicit_oracle_and_dispute_blocks(self):
        for state in ('needs-oracle', 'disputed'):
            registry, cases = self.approve_prerequisites()
            effect = next(case for case in cases if case.name == 'S1_2_001_valid')
            runner.record_fixture_review(registry, cases, effect.review_key, state,
                                         'Explicitly unresolved synthetic premise.', [])
            registry.execution.record_review(cases, 'whole-suite', 'source-reviewed',
                                             'Inventory reviewed, including the unresolved member.')
            aggregate = self.report(registry, cases)
            with self.subTest(state=state):
                self.assertEqual(aggregate['state'], 'current')
                self.assertFalse(aggregate['all_members_approved'])
                self.assertEqual(aggregate['members_needing_approval'][0]['id'], effect.name)
                self.assertEqual(aggregate['members_needing_approval'][0]['state'], state)
                result = self.project(aggregate, self.results(aggregate))['observations'][0]
                self.assertEqual(result['cohorts']['runtime-effect']['outcomes'], {'pass': 1})
                self.assertEqual(result['cohorts']['runtime-effect']['qualified_pass'], 0)
                self.assertFalse(result['all_declared_valid_expectations_qualified'])
                self.assertEqual(self.cli('--audit')[0], 1)
                self.assertEqual(self.cli('-t', effect.name)[0], 1)
                self.assertEqual(self.cli('--update-xfail', '-t', effect.name)[0], 2)
                self.assertEqual(self.cli('--update-xfail', '-t', 'C601_control')[0], 0)

    def test_unknown_duplicate_filtered_or_credit_claiming_contracts_fail(self):
        mutations = [
            lambda data: data.update(scope='selected-cases'),
            lambda data: data.update(coverage_credit='complete'),
            lambda data: data.update(members=['C601_control']),
            lambda data: data.update(id=''),
            lambda data: data['target'].update(requirement='C601'),
            lambda data: data['target'].update(facet='absent'),
            lambda data: data['target'].update(source_units=['1.2#p1']),
            lambda data: data.update(basis=['1.1#absent']),
        ]
        for modify in mutations:
            value = copy.deepcopy(self.aggregate)
            modify(value)
            self.write_aggregates([value])
            with self.subTest(value=value), self.assertRaises(SuiteError):
                self.registry()
        self.write_aggregates([self.aggregate, self.aggregate])
        with self.assertRaisesRegex(SuiteError, 'duplicate'):
            self.registry()

    def test_added_removed_or_unselected_changed_members_stale_the_review(self):
        registry, cases = self.approve()
        snapshot = registry.execution.snapshot(cases)
        selected = next(case for case in cases if case.rule == 'S1.2-001')
        fingerprint = selected.fingerprint(registry)
        path = self.tests / 'control/source.f90'
        path.write_text(path.read_text() + '! changed unselected input\n')
        self.assertEqual(self.report()['state'], 'stale')
        with patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'Registry', side_effect=self.registry):
            errors = runner.confirm_snapshot([], [selected], {selected.review_key: fingerprint},
                                              execution_snapshot=snapshot)
        self.assertTrue(any('complete case universe' in error for error in errors))
        registry, cases = self.approve()
        without = [case for case in cases if case.name != 'C601_control']
        self.assertEqual(self.report(registry, without)['state'], 'stale')
        extra = self.tests / 'C601_valid__extra.f90'
        extra.write_text('! rule: C601\n! evidence: positive-control\nprogram extra\nend program\n')
        self.assertEqual(self.report()['state'], 'stale')

    def test_source_census_and_unrelated_catalogue_material_are_bound(self):
        self.approve()
        self.change('source.json', lambda data: data['sections']['1.2']['units']['p2'].update(sha256='f' * 64))
        self.assertEqual(self.report()['state'], 'stale')
        self.approve()
        self.change('direct.json', lambda data: data['requirements'][0].update(dependencies='New premise.'))
        self.assertEqual(self.report()['state'], 'stale')

    def test_same_basename_with_different_sources_cannot_share_review_fingerprints(self):
        first = self.tests / 'a/C601_invalid.f90'
        first.parent.mkdir()
        first.write_text('! case: first\nprogram first\n'
                         'integer :: x, x ! {error C601 first}\nend program first\n')
        registry, cases = self.approve()
        original = next(case for case in cases if case.name == 'C601_invalid:first')
        second = self.tests / 'b/C601_invalid.f90'
        second.parent.mkdir()
        second.write_text('! case: second\nprogram second\n'
                          'real :: y, y ! {error C601 second}\nend program second\n')
        with self.assertRaisesRegex(SuiteError, 'review group has inconsistent inputs'):
            runner.collect_cases(self.tests, registry, patterns=['C601_control'])
        isolated = next(iter(runner.isolated_cases(str(second), 'C601')))
        conflicting = runner.SuiteCase('C601_invalid:second', 'C601', 'invalid', str(second),
                                      original.meta, original.review_key, isolated=isolated)
        with self.assertRaisesRegex(SuiteError, 'review group has inconsistent inputs'):
            registry.execution.report(cases + [conflicting])

    def test_filtered_run_keeps_the_complete_population_and_missing_effects(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = [row for row in self.results(aggregate) if row['name'] == 'C601_control']
        result = self.project(aggregate, rows)['observations'][0]
        self.assertEqual(result['population'], 5)
        self.assertEqual(result['conforming_candidate_population'], 4)
        self.assertFalse(result['observation_set_complete'])
        self.assertFalse(result['all_declared_valid_expectations_qualified'])
        self.assertEqual(result['cohorts']['runtime-effect']['outcomes'], {'not-selected': 1})
        self.assertEqual(result['cohorts']['positive-control']['qualified_pass'], 1)
        self.assertEqual(result['cohorts']['positive-control']['runtime_effect_pass'], 0)

    def test_full_observations_keep_context_controls_and_diagnostics_separate(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        result = self.project(aggregate, self.results(aggregate))['observations'][0]
        self.assertTrue(result['observation_set_complete'])
        self.assertTrue(result['all_declared_valid_expectations_qualified'])
        self.assertEqual(result['cohorts']['runtime-effect']['runtime_effect_pass'], 1)
        self.assertEqual(result['cohorts']['positive-control']['qualified_pass'], 2)
        self.assertEqual(result['cohorts']['positive-control']['runtime_attempted'], 1)
        self.assertEqual(result['cohorts']['context-only']['runtime_effect_pass'], 0)
        self.assertEqual(result['cohorts']['diagnostic-only']['qualified_pass'], 0)
        bad = next(member for member in result['members'] if member['id'] == 'C601_bad')
        self.assertEqual(bad['outcome'], 'pass')
        self.assertNotIn('missing-successful-declared-phase-trace', bad['qualification_issues'])

    def test_valid_population_presence_does_not_claim_all_diagnostics_were_observed(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = [row for row in self.results(aggregate) if row['kind'] == 'valid']
        result = self.project(aggregate, rows)['observations'][0]
        self.assertFalse(result['observation_set_complete'])
        self.assertTrue(result['valid_observation_set_complete'])
        self.assertTrue(result['all_declared_valid_expectations_qualified'])
        self.assertEqual(result['cohorts']['diagnostic-only']['outcomes'], {'not-selected': 1})

    def test_xfails_and_resource_explanations_do_not_remove_failures(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = self.results(aggregate)
        row = next(item for item in rows if item['name'] == 'S1_2_001_valid')
        row['status'] = 'XFAIL'
        row['check'].update(outcome='fail', phase='compile', note='out of memory',
                            trace=row['check']['trace'][:1])
        row['check']['trace'][0]['returncode'] = 1
        result = self.project(aggregate, rows)['observations'][0]
        self.assertEqual(result['cohorts']['runtime-effect']['population'], 1)
        self.assertEqual(result['cohorts']['runtime-effect']['outcomes'], {'fail': 1})
        self.assertEqual(result['cohorts']['runtime-effect']['runtime_attempted'], 0)
        self.assertFalse(result['all_declared_valid_expectations_qualified'])

    def test_phase_trace_and_input_hashes_are_not_inferred_from_a_pass_label(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        mutations = [
            lambda check: check.update(phase='compile'),
            lambda check: check.update(trace=check['trace'][:1]),
            lambda check: check['trace'][-1].update(timed_out=True),
            lambda check: check['trace'][-1].update(returncode=139),
            lambda check: check['trace'].append(dict(check['trace'][-1], returncode=1)),
            lambda check: check.update(input_hashes={}),
        ]
        for mutate in mutations:
            rows = self.results(aggregate)
            mutate(next(row for row in rows if row['name'] == 'S1_2_001_valid')['check'])
            with self.subTest(mutate=mutate), self.assertRaises(SuiteError):
                self.project(aggregate, rows)

    def test_standard_mode_is_qualified_per_compiler_and_case(self):
        path = self.tests / 'S1_2_001_valid.f90'
        path.write_text('! standard: f2023\n' + path.read_text())
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = self.results(aggregate, references=['flang'], identities={'flang': self.identity('flang', 'f2018')})
        result = self.project(aggregate, rows, [self.identity(), self.identity('flang', 'f2018')])
        self.assertEqual(result['observations'][0]['cohorts']['runtime-effect']['qualified_pass'], 1)
        self.assertEqual(result['observations'][1]['cohorts']['runtime-effect']['qualified_pass'], 0)
        self.assertEqual(result['observations'][1]['cohorts']['runtime-effect']['outcomes'], {'pass': 1})

    def test_commands_cannot_be_transplanted_between_compiler_modes(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        identities = {'gfortran': self.identity('gfortran'), 'flang': self.identity('flang', 'f2018')}
        rows = self.results(aggregate, references=list(identities), identities=identities)
        effect = next(row for row in rows if row['name'] == 'S1_2_001_valid')
        effect['references']['gfortran'] = copy.deepcopy(effect['references']['flang'])
        with self.assertRaisesRegex(SuiteError, 'trace command does not match'):
            self.project(aggregate, rows, list(identities.values()), reference_only=True)

    def test_missing_failed_reordered_or_wrong_step_builds_are_consistency_errors(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        for mutate in (
                lambda trace: trace.pop(0),
                lambda trace: trace[0].update(returncode=1),
                lambda trace: trace.reverse(),
                lambda trace: trace[-1].update(step='unrelated-executable'),
                lambda trace: trace[-1]['command'].__setitem__(0, '/unrelated/executable')):
            rows = self.results(aggregate)
            mutate(next(row for row in rows if row['name'] == 'S1_2_001_valid')['check']['trace'])
            with self.subTest(mutate=mutate), self.assertRaises(SuiteError):
                self.project(aggregate, rows)
        rows = self.results(aggregate)
        next(row for row in rows if row['name'] == 'C601_control')['check']['trace'][-1]['step'] = 'wrong-step'
        with self.assertRaisesRegex(SuiteError, 'phase/step order'):
            self.project(aggregate, rows)

    def test_extra_input_and_header_claims_cannot_qualify(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = self.results(aggregate)
        effect = next(row for row in rows if row['name'] == 'S1_2_001_valid')
        effect['check']['input_hashes']['undeclared-extra.f90'] = 'f' * 64
        with self.assertRaisesRegex(SuiteError, 'exact declared input'):
            self.project(aggregate, rows)
        rows = self.results(aggregate)
        effect = next(row for row in rows if row['name'] == 'S1_2_001_valid')
        effect['check']['compiler_headers']['ISO_Fortran_binding.h'] = {}
        with self.assertRaisesRegex(SuiteError, 'header claims do not match'):
            self.project(aggregate, rows)

    def test_reference_only_never_uses_the_combined_reference_check_as_a_target(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = self.results(aggregate, references=['gfortran', 'flang'])
        next(row for row in rows if row['name'] == 'C601_control')['references']['gfortran']['outcome'] = 'fail'
        next(row for row in rows if row['name'] == 'S1_2_001_valid')['references']['flang']['outcome'] = 'fail'
        result = self.project(aggregate, rows, [self.identity('gfortran'), self.identity('flang')],
                              reference_only=True)
        self.assertEqual([item['role'] for item in result['observations']], ['reference', 'reference'])
        self.assertEqual(result['observations'][1]['cohorts']['runtime-effect']['outcomes'], {'fail': 1})
        self.assertEqual(result['observations'][0]['cohorts']['runtime-effect']['outcomes'], {'pass': 1})
        self.assertEqual([item['all_declared_valid_expectations_qualified']
                          for item in result['observations']], [False, False])

    def test_provisional_or_unreviewed_aggregation_keeps_raw_results_without_qualified_passes(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        for current in (True, False):
            value = copy.deepcopy(aggregate)
            if not current:
                value['state'] = 'draft'
            errors = ['compiler changed'] if current else []
            result = self.project(value, self.results(value), run_errors=errors)['observations'][0]
            self.assertEqual(result['cohorts']['runtime-effect']['outcomes'], {'pass': 1})
            self.assertEqual(result['cohorts']['runtime-effect']['qualified_pass'], 0)
            self.assertFalse(result['all_declared_valid_expectations_qualified'])

    def test_wrong_duplicate_unknown_or_truncated_observation_sets_fail(self):
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = self.results(aggregate)
        with self.assertRaisesRegex(SuiteError, 'duplicate execution result'):
            self.project(aggregate, rows + [rows[0]])
        with self.assertRaisesRegex(SuiteError, 'duplicate compiler identity'):
            self.project(aggregate, rows, [self.identity(), self.identity()])
        for key, value in (('rule', 'C999'), ('metadata', {}), ('review', {'fingerprint': '0' * 64})):
            changed = copy.deepcopy(rows)
            changed[0][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(SuiteError, 'input binding'):
                self.project(aggregate, changed)
        changed = copy.deepcopy(rows)
        changed[0]['name'] = 'not-a-member'
        with self.assertRaisesRegex(SuiteError, 'outside.*universe'):
            self.project(aggregate, changed)
        trimmed = copy.deepcopy(aggregate)
        trimmed['members'].pop()
        with self.assertRaisesRegex(SuiteError, 'inconsistent.*universe'):
            self.project(trimmed, rows)

    def test_profiles_need_current_hashes_and_actual_successful_probe_traces(self):
        profiles = self.tests / 'profiles'
        profiles.mkdir()
        (profiles / 'qualified.f90').write_text('program profile\nend program\n')
        source = self.tests / 'S1_2_001_valid.f90'
        source.write_text('! profile: qualified\n' + source.read_text())
        with patch.object(runner, 'HERE', str(self.tests)), patch.object(runner, 'PROFILES', {'qualified'}):
            registry, cases = self.approve()
            aggregate = self.report(registry, cases)
            member = next(item for item in aggregate['members'] if item['id'] == 'S1_2_001_valid')
            rows = self.results(aggregate)
            check = next(row for row in rows if row['name'] == member['id'])['check']
            good = copy.deepcopy(check['profile_checks']['qualified'])
            check['profile_checks'] = {'qualified': good}
            self.assertEqual(self.project(aggregate, rows)['observations'][0]['cohorts']
                             ['runtime-effect']['qualified_pass'], 1)
            for profile in ({}, dict(good, outcome='skip'), dict(good, input_hashes={}),
                            dict(good, trace=good['trace'][:1])):
                check['profile_checks'] = {'qualified': profile}
                with self.assertRaises(SuiteError):
                    self.project(aggregate, rows)
            check.update(outcome='skip', phase='profile', trace=[], input_hashes={},
                         execution_context={},
                         profile_checks={'qualified': dict(good, outcome='skip',
                             trace=[good['trace'][0], dict(good['trace'][1], returncode=77)])})
            result = self.project(aggregate, rows)['observations'][0]
            self.assertEqual(result['cohorts']['runtime-effect']['outcomes'], {'skip': 1})
            self.assertEqual(result['cohorts']['runtime-effect']['population'], 1)
            self.assertEqual(result['cohorts']['runtime-effect']['runtime_attempted'], 0)

    def test_profile_order_source_and_compiler_must_match_actual_probe_commands(self):
        profiles = self.tests / 'profiles'
        profiles.mkdir()
        (profiles / 'qualified.f90').write_text('program profile\nend program\n')
        source = self.tests / 'S1_2_001_valid.f90'
        source.write_text('! profile: qualified\n' + source.read_text())
        with patch.object(runner, 'HERE', str(self.tests)), patch.object(runner, 'PROFILES', {'qualified'}):
            registry, cases = self.approve()
            aggregate = self.report(registry, cases)
            for mutate in (
                    lambda trace: trace.reverse(),
                    lambda trace: trace[0]['command'].__setitem__(0, 'unrelated-compiler'),
                    lambda trace: trace[0]['command'].__setitem__(-3, '/unrelated/profile.f90'),
                    lambda trace: trace[-1]['command'].__setitem__(0, '/unrelated/profile-executable')):
                rows = self.results(aggregate)
                effect = next(row for row in rows if row['name'] == 'S1_2_001_valid')
                mutate(effect['check']['profile_checks']['qualified']['trace'])
                with self.subTest(mutate=mutate), self.assertRaises(SuiteError):
                    self.project(aggregate, rows)

    def test_explicit_status_200_is_not_reclassified_as_a_compiler_crash(self):
        def update(data):
            data.update(oracle_basis='processor-profile', oracle_profile='posix-stop-code',
                        link=dict(objects=['source.o'], output='program'),
                        expect=dict(phase='run', outcome='success', exit_code=200))
        self.change('tests/control/fixture.json', update)
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        result = self.project(aggregate, self.results(aggregate))['observations'][0]
        control = next(member for member in result['members'] if member['id'] == 'C601_control')
        self.assertTrue(control['qualified_pass'])
        self.assertFalse(control['runtime_effect_pass'])

    def test_multiple_images_need_the_recorded_launcher_configuration(self):
        path = self.tests / 'S1_2_001_valid.f90'
        path.write_text('! requires: coarray\n! images: 2\n' + path.read_text())
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = self.results(aggregate)
        with self.assertRaisesRegex(SuiteError, 'no configured launcher'):
            self.project(aggregate, rows)
        configured = dict(self.identity(), launcher=['launcher', '-n', '{images}', '{exe}'])
        with self.assertRaisesRegex(SuiteError, 'trace command does not match'):
            self.project(aggregate, rows, [configured])
        with self.assertRaisesRegex(SuiteError, 'launcher must be an argv list'):
            self.project(aggregate, rows, [dict(configured, launcher=True)])
        member = next(member for member in aggregate['members'] if member['id'] == 'S1_2_001_valid')
        next(row for row in rows if row['name'] == member['id'])['check'] = self.check(member, identity=configured)
        result = self.project(aggregate, rows, [configured])['observations'][0]
        self.assertEqual(result['cohorts']['runtime-effect']['qualified_pass'], 1)

    def test_c_companion_and_binding_header_provenance_are_preserved(self):
        (self.tests / 'control/companion.c').write_text('void companion(void) {}\n')

        def change(data):
            data['files'].append('companion.c')
            data['build'].append(dict(id='companion', source='companion.c', language='c',
                                      output='companion.o', fortran_binding_header=True))
            data['expect']['step'] = 'companion'
        self.change('tests/control/fixture.json', change)
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = self.results(aggregate)
        check = next(row for row in rows if row['name'] == 'C601_control')['check']
        header = dict(path='/synthetic/ISO_Fortran_binding.h', sha256='f' * 64,
                      discovery='synthetic processor query')
        identity = dict(self.identity(), c_binding_header=header)
        check['compiler_headers'] = {'ISO_Fortran_binding.h': header}
        check['input_hashes']['@compiler/ISO_Fortran_binding.h'] = header['sha256']
        companion = dict(command='cc', version='fixed-companion')
        for compiler, cc, expected in ((self.identity(), companion, False),
                                       (identity, None, False), (identity, companion, True)):
            if not expected:
                with self.assertRaises(SuiteError):
                    self.project(aggregate, rows, [compiler], companion=cc)
            else:
                result = self.project(aggregate, rows, [compiler], companion=cc)['observations'][0]
                control = next(member for member in result['members'] if member['id'] == 'C601_control')
                self.assertTrue(control['qualified_pass'])
        check['input_hashes']['@compiler/ISO_Fortran_binding.h'] = '0' * 64
        with self.assertRaisesRegex(SuiteError, 'exact declared input'):
            self.project(aggregate, rows, [identity], companion=companion)

    def test_fortran_build_with_c_link_driver_requires_actual_companion(self):
        self.change('tests/control/fixture.json', lambda data: data.update(
            link=dict(objects=['source.o'], output='program', driver='c'),
            expect=dict(phase='link', outcome='success')))
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        member = next(item for item in aggregate['members'] if item['id'] == 'C601_control')
        self.assertTrue(member['c_companion_required'])
        rows = self.results(aggregate)
        with self.assertRaisesRegex(SuiteError, 'lacks companion identity'):
            self.project(aggregate, rows)
        with self.assertRaisesRegex(SuiteError, 'trace command does not match'):
            self.project(aggregate, rows, companion=dict(command='unrecorded-c-driver', version='other'))
        report = self.root / 'c-link.json'
        status, _, _, _, executions = self.cli(
            '-t', 'C601_control', '--cc', 'configured-linker', '--report', str(report))
        self.assertEqual((status, executions), (0, 1))
        data = json.loads(report.read_text())
        self.assertEqual(data['c_compiler']['command'], 'configured-linker')
        self.assertEqual(data['results'][0]['check']['trace'][-1]['command'][0], 'configured-linker')

    def test_declared_stdin_is_bound_to_the_actual_run_trace(self):
        (self.tests / 'control/input.txt').write_bytes(b'7\n')

        def change(data):
            data['files'].append('input.txt')
            data.update(link=dict(objects=['source.o'], output='program'),
                        run=dict(stdin_file='input.txt'),
                        expect=dict(phase='run', outcome='success'))
        self.change('tests/control/fixture.json', change)
        registry, cases = self.approve()
        aggregate = self.report(registry, cases)
        rows = self.results(aggregate)
        trace = next(row for row in rows if row['name'] == 'C601_control')['check']['trace']
        expected = hashlib.sha256(b'7\n').hexdigest()
        self.assertEqual(trace[-1]['stdin_sha256'], expected)
        self.project(aggregate, rows)
        for observed in (None, 'f' * 64):
            trace[-1]['stdin_sha256'] = observed
            with self.subTest(observed=observed), self.assertRaisesRegex(SuiteError, 'trace stdin'):
                self.project(aggregate, rows)

    def cli(self, *arguments, mutate_check=None):
        registry = self.registry()
        cases = self.cases(registry)
        members = {item['id']: item for item in self.report(registry, cases)['members']}
        output, errors = io.StringIO(), io.StringIO()

        def compiler(command, target, standard, launcher, timeout):
            return runner.Compiler(command, 'lfortran' if target else command,
                                   'f23' if target else 'f2023', version='fixed-version', launcher=launcher)

        def execute(case, comp, *args):
            identity = dict(comp.configuration(), version=comp.version, c_binding_header=comp.c_binding_header)
            check = self.check(members[case.name], identity=identity,
                               companion=dict(command=args[0], version='fixed-companion'))
            if mutate_check:
                mutate_check(check)
            return runner.Check(**check)

        with patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'Registry', return_value=registry), \
                patch.object(runner, 'compiler', side_effect=compiler) as compilers, \
                patch.object(runner, 'execute_case', side_effect=execute) as executions, \
                patch.object(runner, 'tool_version', return_value='fixed-companion'), \
                patch.object(runner, 'confirm_snapshot', return_value=[]), \
                patch.object(sys, 'argv', ['run_tests.py', *arguments]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            status = runner.main()
        return status, output.getvalue(), errors.getvalue(), compilers.call_count, executions.call_count

    def test_cli_audit_and_baseline_require_current_inventory_review(self):
        self.approve_prerequisites()
        self.assertEqual(self.cli('--audit')[0], 1)
        self.assertEqual(self.cli('--audit', '--allow-unreviewed')[0], 0)
        status, _, error, compilers, executions = self.cli('--update-xfail', '-t', 'C601')
        self.assertEqual((status, compilers, executions), (2, 0, 0))
        self.assertIn('unreviewed/stale execution aggregates', error)
        status, _, _, compilers, executions = self.cli(
            '--record-execution-review', 'whole-suite', '--review-state', 'source-reviewed',
            '--review-rationale', 'Independent finite inventory review.')
        self.assertEqual((status, compilers, executions), (0, 0, 0))
        self.assertEqual(self.cli('--audit')[0], 0)

    def test_cli_report_retains_full_inventory_without_extra_execution(self):
        self.approve()
        report = self.root / 'observations.json'
        status, _, _, compilers, executions = self.cli('-t', 'C601_control', '--report', str(report))
        self.assertEqual((status, compilers, executions), (0, 1, 1))
        data = json.loads(report.read_text())
        aggregate = data['execution_aggregates'][0]
        self.assertEqual(aggregate['member_count'], 5)
        self.assertEqual(len(data['results']), 1)
        self.assertFalse(aggregate['observations'][0]['observation_set_complete'])
        self.assertEqual(data['source_audit']['pending_facets'], 1)

    def test_aggregation_consistency_errors_prevent_baseline_updates(self):
        self.approve()
        report = self.root / 'provisional.json'
        with patch.object(runner, 'execution_observations', side_effect=SuiteError('input binding changed')):
            status, _, _, _, executions = self.cli(
                '-t', 'C601_control', '--update-xfail', '--report', str(report))
        self.assertEqual((status, executions), (2, 1))
        self.assertFalse((self.tests / 'expected_failures.txt').exists())
        data = json.loads(report.read_text())
        self.assertTrue(data['run_errors'])
        self.assertTrue(data['execution_aggregates'][0]['provisional'])
        self.assertEqual(data['execution_aggregates'][0]['observations'], [])

    def test_actual_missing_trace_error_prevents_baseline_update(self):
        self.approve()
        report = self.root / 'missing-trace.json'
        with patch.object(runner, 'update_xfail') as update:
            status, _, _, _, executions = self.cli(
                '-t', 'S1_2_001_valid', '--update-xfail', '--report', str(report),
                mutate_check=lambda check: check.update(trace=[]))
        self.assertEqual((status, executions), (2, 1))
        update.assert_not_called()
        data = json.loads(report.read_text())
        self.assertTrue(data['run_errors'])
        self.assertTrue(data['execution_aggregates'][0]['provisional'])


if __name__ == '__main__':
    unittest.main()
