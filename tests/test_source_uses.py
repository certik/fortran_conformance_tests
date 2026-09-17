import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_tests as runner
from suite_data import Registry, SuiteError, case_review_bindings, write_json


class SourceUseTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.tests = self.root / 'tests'
        self.tests.mkdir()
        self.standard = dict(document='synthetic-pin', edition='F2023', sha256='a' * 64)
        self.source = dict(self.standard, sections={
            '1.1': dict(units={'R401': dict(kind='numbered-item', sha256='b' * 64)}),
            '2.1': dict(units={
                'R801': dict(kind='numbered-item', sha256='c' * 64),
                'R804': dict(kind='numbered-item', sha256='d' * 64),
                'C601': dict(kind='numbered-item', sha256='e' * 64),
                'p1': dict(kind='paragraph', sha256='f' * 64)})})
        target = dict(
            schema_version=1, section='1.1', requirements=[
                dict(id='R401', title='Synthetic alias', source='1.1 R401', source_units=['R401'],
                     category='syntax', diagnostic_obligation='required', definition='Synthetic assumed alias.',
                     facets=['uses'], pending={'uses': 'A complete source-use census remains pending.'},
                     oracle_limitation='No execution can establish this source census.')],
            accounting=[dict(unit='R401', disposition='requirements', requirements=['R401'])])
        use = dict(schema_version=1, section='2.1', requirements=[],
                   subunits={'R801': ['R801.list']}, accounting=[
                       dict(unit=unit, disposition='definition', rationale='Synthetic source.')
                       for unit in ('R801', 'R804', 'C601', 'p1', 'R801.list')])
        index = dict(schema_version=1, standard=self.standard, source_inventory='source.json',
                     rule_inventory='rules.txt', reviews='reviews.json',
                     catalogues=['target.json', 'use.json'], source_uses='source-uses.json')
        self.occurrence = dict(term='entity-decl-list', ordinal=1, resolution='target',
                               definition='1.1#R401', dependencies=['2.1#R804'],
                               rationale='Synthetic contextual member dependency.')
        self.inventory = dict(
            id='assumed-list-uses', target=dict(requirement='R401', facet='uses', source_units=['1.1#R401']),
            basis=['2.1#R804'], sections=['2.1'], coverage_credit='none',
            claim='Only the declared source scope.', limitation='No completeness or processor claim.',
            entries=[
                dict(source='2.1#R801', disposition='mapped', rationale='Two synthetic uses.',
                     occurrences=[self.occurrence, dict(self.occurrence, ordinal=2)]),
                dict(source='2.1#C601', disposition='not-applicable', rationale='No selected term.',
                     occurrences=[]),
                dict(source='2.1#p1', disposition='pending', rationale='The remaining context needs review.',
                     occurrences=[dict(self.occurrence, term='object-name', resolution='explicit-override',
                                       definition='2.1#R804', dependencies=[])])])
        for name, value in (('index.json', index), ('source.json', self.source),
                            ('target.json', target), ('use.json', use)):
            write_json(self.root / name, value)
        (self.root / 'rules.txt').write_text('R401 alias\nR801 enclosing\nR804 override\nC601 other\n')
        self.write_inventories([self.inventory])
        for suffix in ('first', 'second'):
            (self.tests / f'C601_valid__{suffix}.f90').write_text('program p\nend program p\n')

    def write_inventories(self, inventories):
        write_json(self.root / 'source-uses.json',
                   dict(schema_version=1, standard=self.standard, inventories=inventories))

    def change(self, name, modify):
        path = self.root / name
        value = json.loads(path.read_text())
        modify(value)
        write_json(path, value)

    def registry(self):
        return Registry(self.root, 'index.json')

    def report(self, registry=None):
        return (registry or self.registry()).source_uses.report()[0]

    def approve_sources(self):
        registry = self.registry()
        for section in registry.catalogues:
            registry.record_catalogue_review(section, 'Independent synthetic source review.')
        return registry

    def approve(self):
        registry = self.approve_sources()
        registry.source_uses.record_review('assumed-list-uses', 'source-reviewed',
                                           'Independent synthetic inventory review, with explicit gaps.')
        return registry

    def cli(self, *arguments, snapshot_errors=None):
        registry = self.registry()
        output, errors = io.StringIO(), io.StringIO()
        compiler = runner.Compiler('synthetic', 'lfortran', 'f23', version='synthetic')
        with patch.object(runner, 'Registry', return_value=registry), \
                patch.object(runner, 'HERE', str(self.tests)), \
                patch.object(runner, 'compiler', return_value=compiler) as compilers, \
                patch.object(runner, 'execute_case', return_value=runner.Check('pass', phase='run')) as execute, \
                patch.object(runner, 'confirm_snapshot', return_value=snapshot_errors or []), \
                patch.object(sys, 'argv', ['run_tests.py', *arguments]), \
                contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = runner.main()
        return code, output.getvalue(), errors.getvalue(), compilers.call_count, execute.call_count

    def test_scope_derives_all_base_and_fine_units_including_omissions(self):
        report = self.report()
        self.assertEqual((report['source_unit_count'], report['base_source_unit_count'],
                          report['fine_source_unit_count']), (5, 4, 1))
        self.assertEqual(report['disposition_counts'],
                         dict(mapped=1, **{'not-applicable': 1}, pending=1, missing=2))
        self.assertEqual(report['occurrence_record_count'], 3)
        self.assertFalse(report['classified_scope'])
        self.assertEqual({member['source'] for member in report['members']},
                         {'2.1#R801', '2.1#R804', '2.1#C601', '2.1#p1', '2.1#R801.list'})
        self.assertEqual(report['state'], 'draft')

    def test_deleting_all_entries_keeps_the_denominator_and_exposes_missing_rows(self):
        self.inventory['entries'] = []
        self.write_inventories([self.inventory])
        report = self.report()
        self.assertEqual(report['source_unit_count'], 5)
        self.assertEqual(report['disposition_counts']['missing'], 5)
        self.assertEqual(report['occurrence_record_count'], 0)
        self.assertFalse(report['classified_scope'])

    def test_current_partial_inventory_does_not_approve_cases_or_clear_a_facet(self):
        before = self.registry()
        cases = runner.collect_cases(self.tests, before)
        bindings = case_review_bindings(cases, before)
        registry = self.approve()
        report = self.report(registry)
        self.assertEqual(report['state'], 'current')
        self.assertFalse(report['classified_scope'])
        self.assertEqual(report['facet_completion'], 'pending')
        self.assertEqual(report['universal_conformance'], 'not-established')
        self.assertEqual(report['new_executions'], 0)
        self.assertEqual(report['observation_aggregation'], 'not-applicable')
        self.assertEqual(case_review_bindings(runner.collect_cases(self.tests, registry), registry), bindings)
        self.assertEqual(registry.reviews, {})
        audit = registry.audit(cases)
        self.assertEqual((audit['authored_facets'], audit['linked_facets'], audit['pending_facets']), (0, 0, 1))
        self.assertEqual(audit['current_source_use_inventories'], 1)
        self.assertFalse(audit['complete_source'])

    def test_fully_classified_finite_scope_still_does_not_complete_the_target(self):
        for source in ('2.1#R804', '2.1#R801.list'):
            self.inventory['entries'].append(dict(source=source, disposition='not-applicable',
                                                  rationale='Synthetic finite scope judgment.', occurrences=[]))
        self.inventory['entries'][2]['disposition'] = 'mapped'
        self.write_inventories([self.inventory])
        report = self.report(self.approve())
        self.assertTrue(report['classified_scope'])
        self.assertEqual(report['facet_completion'], 'pending')
        self.assertEqual(report['new_executions'], 0)

    def test_source_review_precedes_inventory_review_but_not_fixture_review(self):
        registry = self.registry()
        with self.assertRaisesRegex(SuiteError, 'catalogue source review'):
            registry.source_uses.record_review('assumed-list-uses', 'source-reviewed', 'Premature.')
        registry = self.approve_sources()
        registry.source_uses.record_review('assumed-list-uses', 'source-reviewed', 'Independent source only.')
        self.assertEqual(self.report()['state'], 'current')
        self.assertFalse(registry.reviews)

    def test_a_missing_dependency_catalogue_is_an_explicit_blocker(self):
        self.change('index.json', lambda value: value['catalogues'].remove('target.json'))
        with self.assertRaisesRegex(SuiteError, 'structured requirement'):
            self.registry()
        self.change('index.json', lambda value: value['catalogues'].append('target.json'))
        self.change('index.json', lambda value: value['catalogues'].remove('use.json'))
        report = self.report()
        self.assertIn('2.1: catalogue source review is missing', report['blockers'])
        self.assertEqual(report['source_unit_count'], 4)
        with self.assertRaisesRegex(SuiteError, 'review is missing'):
            self.registry().source_uses.record_review('assumed-list-uses', 'source-reviewed', 'Premature.')

    def test_independent_nonapproval_states_and_unknown_review_targets(self):
        registry = self.registry()
        for state in ('unreviewed', 'disputed', 'needs-oracle'):
            with self.subTest(state=state):
                registry.source_uses.record_review('assumed-list-uses', state, 'Explicitly not approved.')
                self.assertEqual(self.report()['state'], state)
        with self.assertRaisesRegex(SuiteError, 'not reference validation'):
            registry.source_uses.record_review('assumed-list-uses', 'reference-validated', 'No.')
        with self.assertRaisesRegex(SuiteError, 'unknown source-use inventory'):
            registry.source_uses.record_review('typo', 'source-reviewed', 'No.')

    def test_source_reviews_are_exactly_content_bound_and_can_be_renewed(self):
        registry = self.approve()
        before = registry.source_uses.snapshot()
        self.change('use.json', lambda value: value['accounting'][0].update(rationale='A corrected scope.'))
        self.assertEqual(self.report()['state'], 'stale')
        self.assertNotEqual(self.registry().source_uses.snapshot(), before)
        with self.assertRaisesRegex(SuiteError, 'source review is stale'):
            self.registry().source_uses.record_review('assumed-list-uses', 'source-reviewed', 'Too early.')
        self.assertEqual(self.report(self.approve())['state'], 'current')

    def test_every_inventory_and_target_change_invalidates_the_review(self):
        mutations = [
            ('claim', lambda value: value['inventories'][0].update(claim='A different claim.')),
            ('entry', lambda value: value['inventories'][0]['entries'].pop()),
            ('context', lambda value: value['inventories'][0]['entries'][0].update(rationale='New premise.')),
            ('occurrence', lambda value: value['inventories'][0]['entries'][0]['occurrences'][0].update(
                term='other-list')),
            ('dependency', lambda value: value['inventories'][0]['entries'][0]['occurrences'][0].update(
                dependencies=[])),
            ('scope', lambda value: value['inventories'][0]['sections'].append('1.1')),
        ]
        for label, mutate in mutations:
            with self.subTest(label=label):
                self.write_inventories([copy.deepcopy(self.inventory)])
                self.approve()
                self.change('source-uses.json', mutate)
                self.assertEqual(self.report()['state'], 'stale')
        self.write_inventories([copy.deepcopy(self.inventory)])
        self.approve()
        self.change('target.json', lambda value: value['requirements'][0]['pending'].update(
            uses='A corrected pending plan.'))
        self.assertEqual(self.report()['state'], 'stale')

    def test_new_and_removed_fine_units_stale_without_preventing_readjudication(self):
        self.approve()
        def add(value):
            value['subunits']['R801'].append('R801.other')
            value['accounting'].append(dict(unit='R801.other', disposition='definition',
                                            rationale='New source subdivision.'))
        self.change('use.json', add)
        report = self.report()
        self.assertEqual(report['state'], 'stale')
        self.assertEqual(report['source_unit_count'], 6)
        self.assertEqual(report['disposition_counts']['missing'], 3)
        self.approve()
        def remove(value):
            value['subunits']['R801'].remove('R801.other')
            value['accounting'] = [row for row in value['accounting'] if row['unit'] != 'R801.other']
        self.change('use.json', remove)
        self.assertEqual(self.report()['state'], 'stale')
        self.assertEqual(self.report()['source_unit_count'], 5)
        self.assertEqual(self.report(self.approve())['state'], 'current')

    def test_new_base_unit_cannot_disappear_from_the_denominator(self):
        self.approve()
        self.change('source.json', lambda value: value['sections']['2.1']['units'].update(
            note=dict(kind='note', sha256='1' * 64)))
        self.change('use.json', lambda value: value['accounting'].append(
            dict(unit='note', disposition='informative', rationale='Additional pinned source unit.')))
        report = self.report()
        self.assertEqual(report['source_unit_count'], 6)
        self.assertEqual(report['base_source_unit_count'], 5)
        self.assertEqual(report['disposition_counts']['missing'], 3)
        self.assertEqual(report['state'], 'stale')

    def test_review_sources_cannot_be_omitted_or_added_to_a_current_receipt(self):
        for modify in (lambda row: row['sources'].pop(),
                       lambda row: row['sources'].append('2.1#historical')):
            with self.subTest(modify=modify):
                self.write_inventories([copy.deepcopy(self.inventory)])
                self.approve()
                self.change('source-uses.json', lambda value: modify(value['inventories'][0]['review']))
                self.assertEqual(self.report()['state'], 'stale')
                self.assertEqual(self.report(self.approve())['state'], 'current')

    def test_unrelated_cases_and_sections_do_not_change_source_use_evidence(self):
        registry = self.approve()
        snapshot = registry.source_uses.snapshot()
        (self.tests / 'C601_valid__first.f90').write_text('program changed\nend program changed\n')
        self.change('source.json', lambda value: value['sections'].update({
            '3.1': dict(units={'p1': dict(kind='paragraph', sha256='2' * 64)})}))
        self.assertEqual(self.registry().source_uses.snapshot(), snapshot)
        self.assertEqual(self.report()['state'], 'current')

    def test_malformed_inventory_contracts_are_rejected(self):
        mutations = [
            lambda row: row.update(id='invalid id'),
            lambda row: row.update(coverage_credit='complete'),
            lambda row: row.update(sections=[]),
            lambda row: row.update(sections=['2.1', '2.1']),
            lambda row: row.update(sections=['unknown']),
            lambda row: row.update(sections=[' ']),
            lambda row: row.update(entries={}),
            lambda row: row.update(basis=[]),
            lambda row: row.update(basis=['2.1#unknown']),
            lambda row: row['target'].update(requirement='C601'),
            lambda row: row['target'].update(facet='unknown'),
            lambda row: row['target'].update(source_units=[]),
            lambda row: row['target'].update(source_units=['2.1#R801']),
            lambda row: row['entries'].append(copy.deepcopy(row['entries'][0])),
            lambda row: row['entries'][0].update(source='1.1#R401'),
            lambda row: row['entries'][0].update(source='2.1#unknown'),
            lambda row: row['entries'][0].update(disposition='accepted'),
            lambda row: row['entries'][0].update(disposition=[]),
            lambda row: row['entries'][0].update(occurrences=[]),
            lambda row: row['entries'][0].update(occurrences={}),
            lambda row: row['entries'][0].update(disposition='not-applicable'),
            lambda row: row['entries'][0].update(rationale=' '),
            lambda row: row['entries'][0]['occurrences'].append(copy.deepcopy(row['entries'][0]['occurrences'][0])),
            lambda row: row['entries'][0]['occurrences'][0].update(ordinal=True),
            lambda row: row['entries'][0]['occurrences'][0].update(ordinal=0),
            lambda row: row['entries'][0]['occurrences'][0].update(ordinal=1.0),
            lambda row: row['entries'][0]['occurrences'][0].update(term=' '),
            lambda row: row['entries'][0]['occurrences'][0].update(resolution='inferred'),
            lambda row: row['entries'][0]['occurrences'][0].update(resolution='explicit-override'),
            lambda row: row['entries'][0]['occurrences'][0].update(definition='2.1#R804'),
            lambda row: row['entries'][0]['occurrences'][0].update(dependencies=['2.1#C601']),
            lambda row: row['entries'][0]['occurrences'][0].update(dependencies=['unknown']),
            lambda row: row['entries'][0]['occurrences'][0].update(dependencies=['2.1#R804', '2.1#R804']),
        ]
        for index, modify in enumerate(mutations):
            with self.subTest(mutation=index):
                inventory = copy.deepcopy(self.inventory)
                modify(inventory)
                self.write_inventories([inventory])
                with self.assertRaises(SuiteError):
                    self.registry()

    def test_empty_source_sections_cannot_be_a_denominator(self):
        self.change('source.json', lambda value: value['sections'].update({'3.1': dict(units={})}))
        self.inventory['sections'] = ['3.1']
        self.write_inventories([self.inventory])
        with self.assertRaisesRegex(SuiteError, 'unknown or empty source section'):
            self.registry()

    def test_unimplemented_target_cannot_be_removed_from_pending(self):
        self.change('target.json', lambda value: value['requirements'][0].update(pending={}))
        with self.assertRaisesRegex(SuiteError, 'must remain pending'):
            self.registry()

    def test_duplicate_ids_targets_unknown_fields_and_registry_shapes_fail(self):
        for same_target in (False, True):
            other = copy.deepcopy(self.inventory)
            if same_target:
                other['id'] = 'another-id'
            self.write_inventories([self.inventory, other])
            with self.assertRaisesRegex(SuiteError, 'duplicate source-use inventory ID or target'):
                self.registry()
        for layer in ('registry', 'inventory', 'target', 'entry', 'occurrence', 'review'):
            with self.subTest(layer=layer):
                self.write_inventories([copy.deepcopy(self.inventory)])
                self.approve()
                def extra(value):
                    row = value['inventories'][0]
                    target = {'registry': value, 'inventory': row, 'target': row['target'],
                              'entry': row['entries'][0], 'occurrence': row['entries'][0]['occurrences'][0],
                              'review': row['review']}[layer]
                    target['unexpected'] = True
                self.change('source-uses.json', extra)
                with self.assertRaisesRegex(SuiteError, 'unknown fields'):
                    self.registry()
        for field, value in (('schema_version', True), ('schema_version', 2),
                              ('inventories', {}), ('standard', {})):
            self.write_inventories([copy.deepcopy(self.inventory)])
            self.change('source-uses.json', lambda row: row.update({field: value}))
            with self.assertRaises(SuiteError):
                self.registry()

    def test_duplicate_json_fields_and_noncanonical_registry_paths_fail(self):
        path = self.root / 'source-uses.json'
        raw = path.read_text()
        path.write_text(raw.replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'))
        with self.assertRaisesRegex(SuiteError, 'duplicate JSON field'):
            self.registry()
        path.write_text(raw)
        for name in ('./source-uses.json', '../source-uses.json', str(path), 'absent.json'):
            with self.subTest(path=name):
                self.change('index.json', lambda value: value.update(source_uses=name))
                with self.assertRaises(SuiteError):
                    self.registry()

    def test_malformed_review_fields_cannot_become_an_approval(self):
        for field, value in (('state', 'reference-validated'), ('state', []), ('rationale', ''),
                              ('fingerprint', '1'), ('sources', []), ('sources', ['not-an-anchor'])):
            self.write_inventories([copy.deepcopy(self.inventory)])
            self.approve()
            self.change('source-uses.json', lambda row: row['inventories'][0]['review'].update({field: value}))
            with self.assertRaises(SuiteError):
                self.registry()

    def test_cli_adjudication_needs_no_selected_execution_or_compiler(self):
        self.approve_sources()
        result = self.cli('--record-source-use-review', 'assumed-list-uses',
                          '--review-state', 'source-reviewed', '--review-rationale', 'Independent source review.',
                          '-t', 'no-such-execution')
        self.assertEqual(result[0], 0, result[2])
        self.assertEqual(result[3:], (0, 0))
        self.assertIn('Recorded independent finite source-use review', result[1])
        self.assertEqual(self.report()['state'], 'current')

    def test_cli_source_review_also_works_without_any_fixture(self):
        self.approve_sources()
        for path in self.tests.glob('*.f90'):
            path.unlink()
        result = self.cli('--record-source-use-review', 'assumed-list-uses',
                          '--review-state', 'source-reviewed', '--review-rationale', 'No fixture is needed.')
        self.assertEqual(result[0], 0, result[2])
        self.assertEqual(result[3:], (0, 0))
        self.assertEqual(self.report()['state'], 'current')

    def test_cli_rejects_reference_evidence_and_mixed_operations(self):
        options = [
            [],
            ['--review-state', 'source-reviewed'],
            ['--review-state', 'reference-validated', '--review-rationale', 'No.'],
            ['--review-state', 'source-reviewed', '--review-rationale', 'No.', '--review-report', 'fake.json'],
            ['--review-state', 'source-reviewed', '--review-rationale', 'No.', '--review-source', '1.1#R401'],
            ['--review-state', 'source-reviewed', '--review-rationale', 'No.', '--audit'],
            ['--review-state', 'source-reviewed', '--review-rationale', 'No.', '--update-xfail'],
        ]
        for arguments in options:
            with self.subTest(arguments=arguments), self.assertRaises(SystemExit) as error:
                self.cli('--record-source-use-review', 'assumed-list-uses', *arguments)
            self.assertEqual(error.exception.code, 2)

    def test_selected_run_reports_the_whole_source_scope_without_new_results(self):
        self.approve()
        report_path = self.root / 'observations.json'
        result = self.cli('--allow-unreviewed', '-t', 'first', '--report', str(report_path))
        self.assertEqual(result[0], 0, result[2])
        self.assertEqual(result[4], 1)
        self.assertIn('SOURCE-USE CURRENT', result[1])
        report = json.loads(report_path.read_text())
        self.assertEqual(len(report['results']), 1)
        inventory = report['source_use_inventories'][0]
        self.assertEqual(inventory['source_unit_count'], 5)
        self.assertEqual(inventory['new_executions'], 0)
        self.assertEqual(inventory, report['source_audit']['source_use_inventories'][0])
        self.assertNotIn('observations', inventory)

    def test_a_draft_inventory_does_not_veto_independent_approved_execution_or_baseline(self):
        registry = self.registry()
        cases = runner.collect_cases(self.tests, registry)
        for case in cases:
            runner.record_fixture_review(registry, cases, case.review_key, 'source-reviewed',
                                         'Synthetic independent fixture review.', [])
        result = self.cli('-t', 'first', '--update-xfail')
        self.assertEqual(result[0], 0, result[2])
        self.assertEqual(result[4], 1)
        self.assertIn('SOURCE-USE DRAFT', result[1])
        self.assertEqual(self.report()['state'], 'draft')
        self.assertEqual((self.tests / 'expected_failures.txt').read_text(), '\n')
        self.assertEqual(self.cli('--audit')[0], 1)
        self.assertEqual(self.cli('--audit', '--allow-unreviewed')[0], 0)

    def test_source_snapshot_changes_make_report_evidence_provisional(self):
        registry = self.approve()
        before = registry.source_uses.snapshot()
        self.change('source-uses.json', lambda value: value['inventories'][0]['entries'].pop())
        with patch.object(runner, 'Registry', side_effect=self.registry):
            errors = runner.confirm_snapshot([], [], {}, source_use_snapshot=before)
        self.assertEqual(errors, ['source-use inventory, source scope, dependencies, or reviews changed during the run'])

    def test_provisional_source_snapshot_preserves_baseline_bytes_and_reports_the_error(self):
        registry = self.approve()
        cases = runner.collect_cases(self.tests, registry)
        for case in cases:
            runner.record_fixture_review(registry, cases, case.review_key, 'source-reviewed',
                                         'Synthetic independent fixture review.', [])
        baseline = self.tests / 'expected_failures.txt'
        retained = b'C601_valid__unselected  # preserve this exact historical note\n'
        baseline.write_bytes(retained)
        report_path = self.root / 'provisional.json'
        errors = ['source-use inventory changed during the run']
        result = self.cli('-t', 'first', '--update-xfail', '--report', str(report_path), snapshot_errors=errors)
        self.assertEqual(result[0], 2)
        self.assertEqual(baseline.read_bytes(), retained)
        self.assertIn('not modified', result[1])
        report = json.loads(report_path.read_text())
        self.assertEqual(report['run_errors'], errors)
        self.assertEqual(len(report['results']), 1)
        self.assertEqual(report['source_use_inventories'][0]['new_executions'], 0)

    def test_list_exposes_draft_source_scope_without_running_compilers(self):
        result = self.cli('--list', '-t', 'first')
        self.assertEqual(result[0], 0, result[2])
        self.assertEqual(result[3:], (0, 0))
        self.assertIn('SOURCE-USE DRAFT assumed-list-uses [5 source units; 1 pending; 2 missing;', result[1])

    def test_rationale_only_readjudication_changes_snapshot_not_semantic_identity(self):
        registry = self.approve()
        before = registry.source_uses.snapshot()
        old = self.report(registry)
        registry.source_uses.record_review('assumed-list-uses', 'source-reviewed',
                                           'Changed independent inventory rationale.')
        after = registry.source_uses.snapshot()
        new = self.report(registry)
        self.assertEqual(old['review']['fingerprint'], new['review']['fingerprint'])
        self.assertEqual(old['state'], new['state'])
        self.assertEqual(new['state'], 'current')
        self.assertNotEqual(old['review']['rationale'], new['review']['rationale'])
        self.assertNotEqual(before, after)
        with patch.object(runner, 'Registry', side_effect=self.registry):
            errors = runner.confirm_snapshot([], [], {}, source_use_snapshot=before)
        self.assertEqual(errors, ['source-use inventory, source scope, dependencies, or reviews changed during the run'])

    def test_stale_review_snapshot_binds_hidden_historical_rationale(self):
        self.approve()
        self.change('source-uses.json', lambda value: value['inventories'][0].update(
            claim='A changed claim before the invocation.'))
        registry = self.registry()
        before, old = registry.source_uses.snapshot(), self.report(registry)
        self.change('source-uses.json', lambda value: value['inventories'][0]['review'].update(
            rationale='Changed historical rationale while the receipt is stale.'))
        current = self.registry()
        after, new = current.source_uses.snapshot(), self.report(current)
        self.assertEqual(old['state'], 'stale')
        self.assertEqual(new['state'], 'stale')
        self.assertEqual(old['review'], new['review'])
        self.assertNotEqual(before, after)
        with patch.object(runner, 'Registry', side_effect=self.registry):
            errors = runner.confirm_snapshot([], [], {}, source_use_snapshot=before)
        self.assertEqual(errors, ['source-use inventory, source scope, dependencies, or reviews changed during the run'])

    def test_real_cli_snapshot_guards_rereviews_in_reports_and_baseline_updates(self):
        selected = b'C601_valid__first  # original selected canary\n'
        unselected = b'C601_valid__unselected  # preserve exactly\n'
        baseline = self.tests / 'expected_failures.txt'
        report_path = self.root / 'real-snapshot-report.json'
        for update in (False, True):
            for mutation in ('none', 'inventory-review', 'entry', 'prerequisite-review'):
                with self.subTest(update=update, mutation=mutation):
                    self.write_inventories([copy.deepcopy(self.inventory)])
                    registry = self.approve()
                    cases = runner.collect_cases(self.tests, registry)
                    for case in cases:
                        runner.record_fixture_review(registry, cases, case.review_key, 'source-reviewed',
                                                     'Synthetic independent fixture review.', [])
                    baseline.write_bytes(selected + unselected)

                    def execute(*args):
                        current = self.registry()
                        if mutation == 'inventory-review':
                            current.source_uses.record_review(
                                'assumed-list-uses', 'source-reviewed', 'New rationale during the actual snapshot.')
                        elif mutation == 'entry':
                            self.change('source-uses.json', lambda value: value['inventories'][0]['entries'][0].update(
                                rationale='Changed entry rationale during the invocation.'))
                        elif mutation == 'prerequisite-review':
                            current.record_catalogue_review('2.1', 'Changed prerequisite review during the invocation.')
                        return runner.Check('pass', phase='run')

                    compiler = runner.Compiler('synthetic', 'lfortran', 'f23', version='synthetic')
                    arguments = ['run_tests.py', '-t', 'first', '--report', str(report_path)]
                    if update:
                        arguments.append('--update-xfail')
                    with patch.object(runner, 'HERE', str(self.tests)), \
                            patch.object(runner, 'Registry', side_effect=self.registry), \
                            patch.object(runner, 'compiler', return_value=compiler), \
                            patch.object(runner, 'execute_case', side_effect=execute) as executions, \
                            patch.object(sys, 'argv', arguments), \
                            contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        code = runner.main()
                    report = json.loads(report_path.read_text())
                    self.assertEqual(executions.call_count, 1)
                    self.assertEqual(len(report['results']), 1)
                    self.assertEqual(report['source_use_inventories'][0]['source_unit_count'], 5)
                    if mutation == 'none':
                        self.assertEqual(code, 1)
                        self.assertEqual(report['run_errors'], [])
                        self.assertEqual(baseline.read_bytes(), unselected if update else selected + unselected)
                    else:
                        self.assertEqual(code, 2)
                        self.assertEqual(report['run_errors'], [
                            'source-use inventory, source scope, dependencies, or reviews changed during the run'])
                        self.assertEqual(baseline.read_bytes(), selected + unselected)

    def test_absent_or_empty_source_use_registry_keeps_the_default_behavior(self):
        self.write_inventories([])
        self.assertEqual(self.registry().source_uses.report(), [])
        self.change('index.json', lambda value: value.pop('source_uses'))
        registry = self.registry()
        self.assertEqual(registry.source_uses.snapshot(), {})
        self.assertEqual(len(runner.collect_cases(self.tests, registry)), 2)


if __name__ == '__main__':
    unittest.main()
