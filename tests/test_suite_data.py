import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from suite_data import Metadata, Registry, SuiteError, safe_path, write_json


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
