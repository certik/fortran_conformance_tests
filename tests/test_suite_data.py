import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import run_tests as runner
from fixture_support import load_fixture
from suite_data import Metadata, Registry, SuiteError, render_requirement, safe_path, write_json


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        standard = {'document': 'test-document', 'edition': 'F2023', 'sha256': 'a' * 64}
        self.source = dict(standard, sections={
            '1.1': {'units': {'p1': {'kind': 'paragraph'}, 'R601': {'kind': 'numbered-item'}}},
            '1.2': {'units': {'p1': {'kind': 'paragraph'}, 'p2': {'kind': 'paragraph'}}},
            '1.3': {'units': {'p1': {'kind': 'paragraph'}}},
        })
        self.index = dict(schema_version=1, standard=standard, source_inventory='source.json',
                          rule_inventory='rules.txt', catalogues=['a.json', 'b.json'], reviews='reviews.json',
                          source_inventory_review='unreviewed')
        self.a = self.catalogue('1.1', 'one')
        self.a['accounting'].append(dict(unit='R601', disposition='requirements', requirements=['R601']))
        self.b = self.catalogue('1.2', 'two')
        self.b['requirements'][0]['pending'] = {'two': 'Not yet authored.'}
        self.b['accounting'].append(dict(unit='p2', disposition='unresolved', rationale='Not yet extracted.'))
        self.save()
        (self.root / 'rules.txt').write_text('R601 test-rule\n')

    def catalogue(self, section, facet):
        identifier = f'S{section}-001'
        return dict(schema_version=1, section=section, review_state='draft',
                    requirements=[dict(
                        id=identifier, title='Test requirement', source='p1.', source_units=['p1'],
                        category='effect', definition='An independently checked test effect.',
                        diagnostic_obligation='not-required', facets=[facet], pending={},
                        oracle='Check a known result.')],
                    accounting=[dict(unit='p1', disposition='requirements', requirements=[identifier])])

    def save(self):
        for name, value in (('index.json', self.index), ('source.json', self.source),
                            ('a.json', self.a), ('b.json', self.b)):
            write_json(self.root / name, value)

    def registry(self):
        return Registry(self.root, 'index.json')

    def cases(self):
        return [SimpleNamespace(name='one', rule='S1.1-001', kind='valid',
                                meta=Metadata(facets=['one']))]

    def fixture_case(self, name='control', rule='S1.1-001', facets=None,
                     evidence='positive-control', phase='run', outcome='success', oracle_basis='standard'):
        directory = self.root / 'fixtures' / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'source.f90').write_text('program synthetic_metadata\nend program synthetic_metadata\n')
        expectation = dict(phase=phase, outcome=outcome)
        data = dict(
            schema_version=1, id=name, rule=rule, facets=['one'] if facets is None else facets,
            evidence=evidence, standard='f2023', oracle_basis=oracle_basis, files=['source.f90'],
            build=[dict(id='source', source='source.f90', language='fortran', output='source.o')],
            expect=expectation)
        if phase == 'compile':
            expectation['step'] = 'source'
            if outcome in ('diagnose', 'reject'):
                expectation['diagnostic'] = dict(file='source.f90', line=1, contains_any=['synthetic'])
        else:
            data['link'] = dict(objects=['source.o'], output='program')
            if phase == 'run':
                expectation['exit_code'] = 0
        write_json(directory / 'fixture.json', data)
        fixture = load_fixture(directory / 'fixture.json', runner.PROFILES)
        return runner.SuiteCase(fixture.name, fixture.rule, fixture.kind, str(fixture.path),
                                fixture.meta, fixture.name, fixture=fixture)

    def test_positive_control_facets_are_nonempty_unique_declared_strings(self):
        for value in (None, False, 0, 'one', {}, [], [''], [' '], [None], [1], [[]],
                      ['one', 'one'], ['missing'], ['one', 'missing']):
            with self.subTest(value=value):
                self.a['requirements'][0]['positive_control_facets'] = value
                self.save()
                with self.assertRaises(SuiteError):
                    self.registry()
        self.a['requirements'][0]['positive_control_facets'] = ['one']
        self.save()
        self.assertEqual(self.registry().requirements['S1.1-001']['positive_control_facets'], ['one'])

    def test_positive_control_facets_are_only_for_supplementary_effects(self):
        original = copy.deepcopy(self.a)
        for category in ('restriction', 'syntax', 'undefined-result'):
            with self.subTest(category=category):
                self.a = copy.deepcopy(original)
                self.a['requirements'][0].update(category=category, positive_control_facets=['one'])
                self.save()
                with self.assertRaisesRegex(SuiteError, 'only for supplementary effect'):
                    self.registry()
        self.a = copy.deepcopy(original)
        self.a['requirements'][0].update(id='R601', source_units=['R601'], positive_control_facets=['one'])
        self.a['accounting'][0]['requirements'] = ['R601']
        self.save()
        with self.assertRaisesRegex(SuiteError, 'only for supplementary effect'):
            self.registry()

    def test_default_supplementary_and_numbered_evidence_roles_are_unchanged(self):
        original = copy.deepcopy(self.a)
        defaults = {'effect': 'effect', 'restriction': 'positive-control',
                    'syntax': 'positive-control', 'undefined-result': 'context-only'}
        for numbered in (False, True):
            for category, default in defaults.items():
                self.a = copy.deepcopy(original)
                self.a['requirements'][0]['category'] = category
                if numbered:
                    self.a['requirements'][0].update(id='R601', source_units=['R601'])
                    self.a['accounting'][0]['requirements'] = ['R601']
                self.save()
                registry = self.registry()
                requirement = registry.requirements['R601' if numbered else 'S1.1-001']
                before = copy.deepcopy(requirement)
                for evidence in ('effect', 'positive-control', 'context-only'):
                    case = self.cases()[0]
                    case.rule = requirement['id']
                    case.meta.evidence = evidence
                    with self.subTest(numbered=numbered, category=category, evidence=evidence):
                        allowed = evidence in {'effect', 'positive-control'} if numbered else evidence == default
                        if allowed:
                            registry.validate_cases([case])
                        else:
                            with self.assertRaisesRegex(SuiteError, 'requires .* evidence'):
                                registry.validate_cases([case])
                self.assertEqual(requirement, before)
                self.assertNotIn('positive_control_facets', requirement)

    def test_marked_controls_and_unmarked_effects_require_each_facets_role(self):
        self.a['requirements'][0].update(facets=['one', 'other'], positive_control_facets=['one'])
        self.save()
        registry = self.registry()
        control = self.fixture_case()
        effect = self.fixture_case('effect', facets=['other'], evidence='effect')
        self.assertEqual(registry.validate_cases([control, effect])['S1.1-001'], {'one', 'other'})
        for wrong in ('effect', 'context-only'):
            control.meta.evidence = wrong
            with self.subTest(control_evidence=wrong), self.assertRaisesRegex(SuiteError, 'requires positive-control'):
                registry.validate_cases([control, effect])
        control.meta.evidence = 'positive-control'
        for wrong in ('positive-control', 'context-only'):
            effect.meta.evidence = wrong
            with self.subTest(effect_evidence=wrong), self.assertRaisesRegex(SuiteError, 'requires effect'):
                registry.validate_cases([control, effect])
        for evidence in ('effect', 'positive-control', 'context-only'):
            for facets in (['one', 'other'], ['other', 'one']):
                mixed = self.fixture_case('mixed', facets=facets, evidence=evidence)
                with self.subTest(evidence=evidence, facets=facets), self.assertRaisesRegex(SuiteError, 'incompatible evidence roles'):
                    registry.validate_cases([mixed])
        self.a['requirements'][0]['positive_control_facets'] = ['one', 'other']
        self.save()
        self.registry().validate_cases([self.fixture_case('both', facets=['one', 'other'])])

    def test_control_cases_keep_compile_link_and_run_phases_and_reject_unknown_facets(self):
        self.a['requirements'][0]['positive_control_facets'] = ['one']
        self.save()
        for phase in ('compile', 'link', 'run'):
            case = self.fixture_case(phase=phase)
            self.registry().validate_cases([case])
            self.assertEqual(case.fixture.expectation.phase, phase)
            self.assertEqual(case.meta.evidence, 'positive-control')
        for facets in ([], ['missing'], ['one', 'missing'], ['one', 'one']):
            with self.subTest(facets=facets), self.assertRaises(SuiteError):
                self.registry().validate_cases([self.fixture_case(facets=facets)])

    def test_invalid_control_facets_reject_standard_and_policy_oracles(self):
        for obligation in ('not-required', 'required'):
            self.a['requirements'][0].update(positive_control_facets=['one'], diagnostic_obligation=obligation)
            self.save()
            for basis in ('standard', 'lfortran-policy'):
                for outcome in ('diagnose', 'reject'):
                    case = self.fixture_case(phase='compile', outcome=outcome, evidence='effect', oracle_basis=basis)
                    with self.subTest(obligation=obligation, basis=basis, outcome=outcome):
                        self.assertEqual(case.kind, 'invalid')
                        with self.assertRaisesRegex(SuiteError, 'invalid cases cannot cover positive-control'):
                            self.registry().validate_cases([case])

    def test_opted_in_invalid_effect_facets_cannot_bypass_roles_with_policy(self):
        requirement = self.a['requirements'][0]
        requirement.update(facets=['one', 'control'], pending={'control': 'No control case yet.'})
        for opted_in in (False, True):
            if opted_in:
                requirement['positive_control_facets'] = ['control']
            for obligation in ('not-required', 'required'):
                requirement['diagnostic_obligation'] = obligation
                self.save()
                for basis in ('standard', 'lfortran-policy'):
                    for evidence in ('effect', 'positive-control', 'context-only'):
                        case = self.fixture_case(phase='compile', outcome='diagnose',
                                                 evidence=evidence, oracle_basis=basis)
                        with self.subTest(opted_in=opted_in, obligation=obligation, basis=basis, evidence=evidence):
                            if opted_in and evidence != 'effect':
                                with self.assertRaisesRegex(SuiteError, 'requires effect evidence'):
                                    self.registry().validate_cases([case])
                            elif obligation != 'required' and basis == 'standard':
                                with self.assertRaisesRegex(SuiteError, 'diagnostic-policy basis'):
                                    self.registry().validate_cases([case])
                            else:
                                self.registry().validate_cases([case])

    def test_control_designation_does_not_clear_pending_or_approve_anything(self):
        self.a['requirements'][0].update(positive_control_facets=['one'], pending={'one': 'Not authored.'})
        self.save()
        registry = self.registry()
        pending = copy.deepcopy(registry.requirements['S1.1-001']['pending'])
        registry.validate_cases([])
        self.assertEqual(registry.requirements['S1.1-001']['pending'], pending)
        self.assertEqual(registry.catalogue_review_state('1.1'), 'draft')
        self.assertEqual(registry.reviews, {})
        case = self.fixture_case()
        with self.assertRaisesRegex(SuiteError, 'declared pending'):
            registry.validate_cases([case])
        self.a['requirements'][0]['pending'] = {}
        self.save()
        registry = self.registry()
        registry.validate_cases([case])
        self.assertEqual(registry.review(case.review_key, case.fingerprint(registry)).state, 'unreviewed')
        self.assertEqual(registry.catalogue_review_state('1.1'), 'draft')

    def test_rendered_control_facets_are_explicit_and_absent_by_default(self):
        requirement = self.a['requirements'][0]
        before = render_requirement(requirement)
        self.assertNotIn('Positive-control facets', before)
        requirement['positive_control_facets'] = ['one']
        rendered = render_requirement(requirement)
        line = '**Positive-control facets:** `one`.'
        self.assertIn(line, rendered)
        self.assertEqual(rendered.replace(line + '\n\n', ''), before)

    def test_added_and_changed_control_designations_stale_case_and_source_fingerprints(self):
        self.a['requirements'][0].update(
            facets=['one', 'control', 'other-control'],
            pending={'control': 'No control case yet.', 'other-control': 'No other control case yet.'})
        self.save()
        case = self.fixture_case('effect', evidence='effect')
        input_bytes = case.fixture.inputs()
        registry = self.registry()
        registry.validate_cases([case])
        for controls in (['control'], ['control', 'other-control']):
            registry.record_catalogue_review('1.1', 'Synthetic independent source review before mutation.')
            fingerprint = case.fingerprint(registry)
            registry.record_review(case.review_key, fingerprint, 'source-reviewed',
                                   'Synthetic independent fixture review.', ['1.1#p1'])
            source_fingerprint = registry.catalogue_fingerprint('1.1')
            self.a = json.loads((self.root / 'a.json').read_text())
            self.a['requirements'][0]['positive_control_facets'] = controls
            self.save()
            registry = self.registry()
            registry.validate_cases([case])
            self.assertEqual(case.fixture.inputs(), input_bytes)
            self.assertNotEqual(case.fingerprint(registry), fingerprint)
            self.assertNotEqual(registry.catalogue_fingerprint('1.1'), source_fingerprint)
            self.assertEqual(registry.catalogue_review_state('1.1'), 'stale')
            self.assertEqual(registry.review(case.review_key, case.fingerprint(registry)).state, 'stale')
            self.assertEqual(registry.requirements['S1.1-001']['pending'],
                             {'control': 'No control case yet.', 'other-control': 'No other control case yet.'})

    def test_synthetic_BCS_run_control_requires_explicit_opt_in_without_retention_execution(self):
        self.source['sections']['8.5.5'] = {'units': {'p3': {'kind': 'paragraph'}}}
        self.index['catalogues'].append('bcs.json')
        catalogue = self.catalogue('8.5.5', 'explicit-save-confirmation')
        requirement = catalogue['requirements'][0]
        requirement.update(id='S8.5.5-002', source_units=['p3'],
                           definition='Synthetic evidence-role preflight, not a COMMON retention assertion.',
                           facets=['named-common-retention', 'explicit-save-confirmation'],
                           pending={'named-common-retention': 'No retention program is authored by this test.'})
        catalogue['accounting'] = [dict(unit='p3', disposition='requirements', requirements=['S8.5.5-002'])]
        write_json(self.root / 'bcs.json', catalogue)
        self.save()
        case = self.fixture_case('synthetic_bcs_control', rule='S8.5.5-002', facets=['explicit-save-confirmation'])
        with self.assertRaisesRegex(SuiteError, 'requires effect evidence'):
            self.registry().validate_cases([*self.cases(), case])
        requirement['positive_control_facets'] = ['explicit-save-confirmation']
        write_json(self.root / 'bcs.json', catalogue)
        registry = self.registry()
        registry.validate_cases([*self.cases(), case])
        self.assertEqual((case.fixture.expectation.phase, case.fixture.expectation.exit_code), ('run', 0))
        self.assertEqual(case.meta.evidence, 'positive-control')
        self.assertEqual(registry.catalogue_review_state('8.5.5'), 'draft')
        self.assertFalse(registry.review(case.review_key, case.fingerprint(registry)).approved)
        self.assertEqual(registry.requirements['S8.5.5-002']['pending'],
                         {'named-common-retention': 'No retention program is authored by this test.'})

    def test_multiple_catalogues_are_data_driven(self):
        registry = self.registry()
        self.assertEqual(set(registry.requirements), {'S1.1-001', 'S1.2-001'})
        audit = registry.audit(self.cases())
        self.assertEqual(audit['requirements'], 2)
        self.assertEqual(audit['authored_facets'], 1)
        self.assertEqual(audit['pending_facets'], 1)
        self.assertEqual(audit['unresolved_base_units'], 2)
        self.assertIn('1.3', audit['sections_without_catalogues'])
        self.assertFalse(audit['complete_source'])

    def test_recommendations_account_for_source_without_creating_requirements(self):
        self.b['requirements'] = []
        self.b['accounting'] = [
            dict(unit=unit, disposition='recommendation',
                 rationale='Advisory documentation, not mandatory or implemented evidence.')
            for unit in ('p1', 'p2')]
        self.save()
        registry = self.registry()
        audit = registry.audit(self.cases())
        self.assertEqual(set(registry.requirements), {'S1.1-001'})
        self.assertEqual(audit['requirements'], 1)
        self.assertEqual(audit['authored_facets'], 1)
        self.assertEqual(audit['pending_facets'], 0)
        self.assertEqual(audit['unresolved_base_units'], 1)
        self.assertFalse(audit['complete_source'])
        registry.record_catalogue_review('1.2', 'Reviewed advisory modality.')
        self.b = json.loads((self.root / 'b.json').read_text())
        self.b['accounting'][0]['rationale'] = 'A changed documentary interpretation.'
        self.save()
        self.assertEqual(self.registry().catalogue_review_state('1.2'), 'stale')

    def test_recommendation_needs_a_rationale_and_unknown_dispositions_stay_invalid(self):
        for disposition, rationale in (('recommendation', ''), ('advice', 'Unrecognized category.')):
            with self.subTest(disposition=disposition):
                self.b['accounting'][-1] = dict(
                    unit='p2', disposition=disposition, rationale=rationale)
                self.save()
                with self.assertRaises(SuiteError):
                    self.registry()

    def test_descriptor_review_evidence_requires_header_and_companion_identity(self):
        registry = self.registry()
        header = dict(path='/processor/ISO_Fortran_binding.h', sha256='b' * 64,
                      discovery='compiler-query', cfi_version='1')
        reference = dict(case='one', compiler='gfortran', version='GNU snapshot',
                         standard='f2023', phase='run', outcome='pass',
                         compiler_headers={'ISO_Fortran_binding.h': header},
                         c_compiler=dict(command='cc', version='C snapshot'))
        registry.record_review('one', 'a' * 64, 'reference-validated',
                               'Reviewed descriptor interface.', ['1.1#p1'], [reference])
        for mutate in (
            lambda data: data.pop('c_compiler'),
            lambda data: data.pop('compiler_headers'),
            lambda data: data['compiler_headers']['ISO_Fortran_binding.h'].update(sha256='bad'),
            lambda data: data['c_compiler'].update(version=''),
        ):
            data = copy.deepcopy(reference)
            mutate(data)
            with self.assertRaises(SuiteError):
                registry.record_review('one', 'a' * 64, 'reference-validated',
                                       'Bad interface evidence.', ['1.1#p1'], [data])

    def test_numbered_rules_can_have_structured_facets_too(self):
        item = self.a['requirements'][0]
        item['id'] = 'R601'
        item['category'] = 'syntax'
        item['diagnostic_obligation'] = 'required'
        item['source_units'] = ['R601']
        self.a['accounting'][0]['requirements'] = ['R601']
        self.save()
        case = SimpleNamespace(name='syntax', rule='R601', kind='valid', meta=Metadata(facets=['one']))
        self.registry().validate_cases([case])

    def test_unclassified_paragraph_is_an_error(self):
        self.a['accounting'] = self.a['accounting'][1:]
        self.save()
        with self.assertRaisesRegex(SuiteError, 'unclassified source units'):
            self.registry()

    def test_unknown_source_anchor_is_an_error(self):
        self.a['requirements'][0]['source_units'] = ['p99']
        self.save()
        with self.assertRaisesRegex(SuiteError, 'source anchor'):
            self.registry()

    def test_duplicate_ids_are_an_error(self):
        self.a['requirements'].append(copy.deepcopy(self.a['requirements'][0]))
        self.save()
        with self.assertRaisesRegex(SuiteError, 'duplicate requirement'):
            self.registry()

    def test_pending_facets_are_not_hard_coded_in_python(self):
        self.b['requirements'][0]['facets'].append('another')
        self.b['requirements'][0]['pending']['another'] = 'Needs a new oracle.'
        self.save()
        self.assertEqual(self.registry().audit(self.cases())['pending_facets'], 2)

    def test_missing_facet_cannot_silently_disappear(self):
        with self.assertRaisesRegex(SuiteError, 'uncovered facets'):
            self.registry().validate_cases([])

    def test_implemented_pending_facet_requires_explicit_data_update(self):
        cases = self.cases() + [SimpleNamespace(
            name='two', rule='S1.2-001', kind='valid', meta=Metadata(facets=['two']))]
        with self.assertRaisesRegex(SuiteError, 'declared pending'):
            self.registry().validate_cases(cases)

    def test_context_only_cannot_be_reported_as_effect(self):
        self.a['requirements'][0]['category'] = 'undefined-result'
        self.save()
        with self.assertRaisesRegex(SuiteError, 'context-only'):
            self.registry().validate_cases(self.cases())

    def test_prose_rejection_requires_a_diagnostic_basis(self):
        case = self.cases()[0]
        case.kind = 'invalid'
        with self.assertRaisesRegex(SuiteError, 'diagnostic-policy'):
            self.registry().validate_cases([case])
        case.meta.oracle_basis = 'lfortran-policy'
        self.registry().validate_cases([case])

    def test_required_source_form_diagnostic_is_distinct_from_extra_policy(self):
        self.a['requirements'][0]['diagnostic_obligation'] = 'required'
        self.save()
        case = self.cases()[0]
        case.kind = 'invalid'
        self.registry().validate_cases([case])

    def test_unresolved_subdivision_blocks_source_completeness(self):
        self.a['subunits'] = {'p1': ['p1.remaining']}
        self.a['accounting'].append(dict(unit='p1.remaining', disposition='unresolved',
                                         rationale='Unextracted branch.'))
        self.save()
        audit = self.registry().audit(self.cases())
        self.assertEqual(audit['unresolved_fine_units'], 1)

    def test_source_census_review_is_bound_to_its_bytes(self):
        self.index['source_inventory_review'] = dict(
            state='reviewed', fingerprint=hashlib.sha256((self.root / 'source.json').read_bytes()).hexdigest(),
            rationale='Reviewed synthetic census.')
        self.save()
        self.assertEqual(self.registry().source_review_state, 'reviewed')
        self.source['sections']['1.4'] = {'units': {'p1': {'kind': 'paragraph'}}}
        self.save()
        self.assertEqual(self.registry().source_review_state, 'stale')

    def test_numbered_only_sections_do_not_bypass_catalogue_review(self):
        self.source['sections'] = {
            '1.1': self.source['sections']['1.1'],
            '1.4': {'units': {'R602': {'kind': 'numbered-item'}}},
        }
        self.index['catalogues'] = ['a.json']
        self.save()
        (self.root / 'rules.txt').write_text('R601 test-rule\nR602 other-rule\n')
        self.index['source_inventory_review'] = dict(
            state='reviewed', fingerprint=hashlib.sha256((self.root / 'source.json').read_bytes()).hexdigest(),
            rationale='Reviewed synthetic source census.')
        self.save()
        registry = self.registry()
        registry.record_catalogue_review('1.1', 'Reviewed all local units.')
        audit = registry.audit(self.cases())
        self.assertEqual(audit['unresolved_base_units'], 0)
        self.assertEqual(audit['catalogue_reviews'], {'1.1': 'reviewed'})
        self.assertEqual(audit['sections_without_catalogues'], ['1.4'])
        self.assertFalse(audit['complete_source'])

    def test_catalogue_review_is_bound_to_subdivisions_and_accounting(self):
        self.a['subunits'] = {'p1': ['p1.remaining']}
        self.a['accounting'].append(dict(unit='p1.remaining', disposition='unresolved',
                                         rationale='Not yet extracted.'))
        self.save()
        registry = self.registry()
        registry.record_catalogue_review('1.1', 'Reviewed the explicit remaining source gap.')
        self.assertEqual(self.registry().catalogue_review_state('1.1'), 'reviewed')
        registry.catalogues['1.1'].pop('subunits')
        registry.catalogues['1.1']['accounting'] = [
            item for item in registry.catalogues['1.1']['accounting'] if item['unit'] != 'p1.remaining']
        self.assertEqual(registry.catalogue_review_state('1.1'), 'stale')

    def test_catalogue_review_is_bound_to_source_census_content(self):
        registry = self.registry()
        registry.record_catalogue_review('1.1', 'Reviewed the source and definitions.')
        registry.sections['1.1']['units']['p1']['sha256'] = 'f' * 64
        self.assertEqual(registry.catalogue_review_state('1.1'), 'stale')

    def test_unfingerprinted_catalogue_review_is_not_current(self):
        self.a['review_state'] = 'reviewed'
        self.save()
        self.assertEqual(self.registry().catalogue_review_state('1.1'), 'stale')

    def test_missing_numbered_rule_is_not_hidden_by_census(self):
        (self.root / 'rules.txt').write_text('R601 test-rule\nC601 missing-rule\n')
        with self.assertRaisesRegex(SuiteError, 'numbered-rule inventory'):
            self.registry()

    def test_generated_view_is_checked_not_maintained_twice(self):
        self.a['render'] = {'path': 'a.md'}
        (self.root / 'a.md').write_text('Header\n<!-- BEGIN GENERATED 1.1 -->\nold\n<!-- END GENERATED 1.1 -->\n')
        self.save()
        registry = self.registry()
        with self.assertRaisesRegex(SuiteError, 'stale'):
            registry.render()
        registry.render(write=True)
        registry.render()
        self.assertIn('### S1.1-001', (self.root / 'a.md').read_text())

    def test_approval_is_bound_to_fixture_and_definition(self):
        registry = self.registry()
        inputs = {'source.f90': b'end\n'}
        fingerprint = registry.fingerprint('S1.1-001', inputs)
        registry.record_review('one', fingerprint, 'source-reviewed', 'Checked the effect.', ['1.1#p1'])
        self.assertTrue(registry.review('one', fingerprint).approved)
        changed = registry.fingerprint('S1.1-001', {'source.f90': b'program changed\nend\n'})
        self.assertEqual(registry.review('one', changed).state, 'stale')
        registry.requirements['S1.1-001']['definition'] = 'Changed meaning.'
        changed = registry.fingerprint('S1.1-001', inputs)
        self.assertEqual(registry.review('one', changed).state, 'stale')

    def test_reference_approval_needs_evidence(self):
        registry = self.registry()
        with self.assertRaisesRegex(SuiteError, 'no recorded evidence'):
            registry.record_review('one', 'b' * 64, 'reference-validated', 'Claimed.', ['1.1#p1'])

    def test_failed_reference_evidence_cannot_certify_validation(self):
        evidence = [dict(case='one', compiler='reference', version='v1', standard='f2023',
                         phase='run', outcome='fail')]
        with self.assertRaisesRegex(SuiteError, 'successful reference'):
            self.registry().record_review('one', 'b' * 64, 'reference-validated',
                                          'Claimed.', ['1.1#p1'], evidence)

    def test_reference_approval_cannot_omit_cases_in_a_container(self):
        registry = self.registry()
        evidence = [dict(case='one:a', compiler='reference', version='v1', standard='f2023',
                         phase='compile', outcome='pass')]
        registry.record_review('one', 'b' * 64, 'reference-validated', 'Checked a.', ['1.1#p1'], evidence)
        with self.assertRaisesRegex(SuiteError, 'execution set'):
            registry.review('one', 'b' * 64, ['one:a', 'one:b'])

    def test_review_sources_must_exist(self):
        with self.assertRaisesRegex(SuiteError, 'unknown review source'):
            self.registry().record_review('one', 'b' * 64, 'source-reviewed', 'Claimed.', ['1.1#missing'])

    def test_path_escape_is_rejected(self):
        for path in ('../outside', '/tmp/outside', 'a/../../outside'):
            with self.assertRaises(SuiteError):
                safe_path(self.root, path, exists=False)


if __name__ == '__main__':
    unittest.main()
