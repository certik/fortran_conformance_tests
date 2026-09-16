"""Finite role-preserving links to canonical cases, never new executions."""
from dataclasses import asdict
import json
from pathlib import Path
import re

from suite_data import (Review, SuiteError, canonical_evidence_path, digest, fields,
                        read_json, string, strings, write_json)


PATTERNS = {
    'diagnostic-control': {'diagnostic', 'positive-control'},
    'runtime-effect': {'runtime-effect'},
    'positive-control': {'positive-control'},
}
LINK_REVIEW_STATES = {'source-reviewed', 'unreviewed', 'disputed', 'needs-oracle'}


def expected_phase(case):
    return case.fixture.expectation.phase if case.fixture else (
        'run' if case.kind == 'valid' else 'compile')


def qualifying_reference(case, observation):
    modes = {'f2023'} if case.meta.standard == 'f2023' else {'f2018', 'f2023'}
    return (observation['outcome'] == 'pass' and observation['phase'] == expected_phase(case)
            and observation['standard'] in modes)


class EvidenceLinks:
    def __init__(self, registry, filename=None):
        self.registry = registry
        self.path = self._path(filename) if filename is not None else None
        self.data = read_json(self.path, unique_keys=True) if self.path else {
            'schema_version': 1, 'standard': registry.standard, 'links': []}
        fields(self.data, ('schema_version', 'standard', 'links'), (), 'evidence registry')
        if type(self.data['schema_version']) is not int or self.data['schema_version'] != 1:
            raise SuiteError('unsupported evidence-registry schema')
        if self.data['standard'] != registry.standard:
            raise SuiteError('evidence registry does not match the pinned standard')
        if not isinstance(self.data['links'], list):
            raise SuiteError('evidence links must be a list')
        self.links = {}
        targets = set()
        for link in self.data['links']:
            self._link(link)
            name = link['id']
            target = (link['target']['requirement'], link['target']['facet'])
            if name in self.links or target in targets:
                raise SuiteError(f'{name}: duplicate link ID or target facet')
            self.links[name] = link
            targets.add(target)

    def _path(self, relative):
        return canonical_evidence_path(self.registry.root, relative)

    def _source(self, anchor):
        return self.registry.source_material(anchor)

    def _link(self, link):
        fields(link, ('id', 'target', 'basis', 'claim', 'limitation', 'cases'),
               ('pattern', 'review'), 'evidence link')
        name = string(link['id'], 'link ID')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]*', name):
            raise SuiteError(f'{name}: invalid link ID')
        pattern = string(link.get('pattern', 'diagnostic-control'), f'{name}.pattern')
        if pattern not in PATTERNS:
            raise SuiteError(f'{name}: unknown canonical evidence pattern {pattern}')
        target = link['target']
        fields(target, ('requirement', 'facet', 'source_units'), (), f'{name}.target')
        rule = string(target['requirement'], f'{name}.target.requirement')
        requirement = self.registry.requirements.get(rule)
        if not requirement or rule in self.registry.numbered:
            raise SuiteError(f'{name}: target must be a known supplementary requirement; no self/circular links')
        facet = string(target['facet'], f'{name}.target.facet')
        if facet not in requirement['facets']:
            raise SuiteError(f'{name}: unknown target facet {facet}')
        section = self.registry.requirement_sections[rule]
        anchors = {section + '#' + unit for unit in requirement['source_units']}
        sources = strings(target['source_units'], f'{name}.target.source_units', nonempty=True)
        if set(sources) - anchors:
            raise SuiteError(f'{name}: target source is not anchored to its requirement')
        basis = strings(link['basis'], f'{name}.basis', nonempty=True)
        for anchor in sources + basis:
            self._source(anchor)
        for key in ('claim', 'limitation'):
            string(link[key], f'{name}.{key}')
        if not isinstance(link['cases'], list) or not link['cases']:
            raise SuiteError(f'{name}: explicit canonical cases are required')
        identifiers, roles, paths = set(), set(), set()
        for member in link['cases']:
            fields(member, ('id', 'role', 'primary_rule', 'source', 'path', 'phase'), (), f'{name}.case')
            identifier = string(member['id'], f'{name}.case.id')
            role = string(member['role'], f'{name}.case.role')
            primary = string(member['primary_rule'], f'{name}.case.primary_rule')
            phase = string(member['phase'], f'{name}.case.phase')
            path = self._path(member['path'])
            if identifier in identifiers or role in roles or path in paths:
                raise SuiteError(f'{name}: duplicate case ID, role, or path')
            if role not in PATTERNS[pattern]:
                raise SuiteError(f'{name}: canonical case role {role} does not match pattern {pattern}')
            if primary == rule:
                raise SuiteError(f'{name}: a link cannot reuse its target requirement as its primary')
            source = self._source(member['source'])
            if primary in self.registry.numbered:
                primary_sources = {member['source']} if (
                    source['unit'] == primary and source['source']['kind'] == 'numbered-item') else set()
            else:
                primary_requirement = self.registry.requirements.get(primary)
                if not primary_requirement or 'pattern' not in link:
                    raise SuiteError(f'{name}: an S-owned canonical case needs a known requirement and explicit pattern')
                primary_section = self.registry.requirement_sections[primary]
                primary_sources = {primary_section + '#' + unit
                                   for unit in primary_requirement['source_units']}
            if member['source'] not in primary_sources or member['source'] not in basis:
                raise SuiteError(f'{name}: incorrect primary/source relation or missing basis')
            if phase not in ('compile', 'link', 'run'):
                raise SuiteError(f'{name}: unknown canonical case phase {phase}')
            identifiers.add(identifier)
            roles.add(role)
            paths.add(path)
        if roles != PATTERNS[pattern]:
            raise SuiteError(f'{name}: requires exactly the canonical roles for {pattern}')
        if len({member['primary_rule'] for member in link['cases']}) != 1:
            raise SuiteError(f'{name}: the diagnostic/control pair must have the same primary rule')
        if 'review' in link:
            review = link['review']
            fields(review, ('state', 'rationale', 'sources', 'fingerprint'), (), f'{name}.review')
            string(review['state'], f'{name}.review.state')
            string(review['fingerprint'], f'{name}.review.fingerprint')
            self.registry._review_record(name, review)
            if review['state'] not in LINK_REVIEW_STATES:
                raise SuiteError(f'{name}: link adjudication is source review, not reference validation')
            if set(sources + basis) - set(review['sources']):
                raise SuiteError(f'{name}: link review must address every declared source/basis anchor')

    def validate_cases(self, cases):
        by_id = {case.name: case for case in cases}
        if len(by_id) != len(cases):
            raise SuiteError('duplicate execution ID in canonical case set')
        covered = {}
        for link in self.links.values():
            for member in link['cases']:
                case = by_id.get(member['id'])
                if case is None:
                    raise SuiteError(f"{link['id']}: unknown canonical case ID {member['id']}")
                if case.rule != member['primary_rule'] or Path(case.path).resolve() != self._path(member['path']):
                    raise SuiteError(f"{link['id']}: canonical case primary rule or path does not match {case.name}")
                if member['phase'] != expected_phase(case):
                    raise SuiteError(f"{link['id']}: declared phase does not match canonical case {case.name}")
                role = member['role']
                if role == 'diagnostic':
                    matches = (case.kind == 'invalid' and member['phase'] == 'compile'
                               and case.meta.evidence == 'effect')
                elif role == 'positive-control':
                    matches = case.kind == 'valid' and case.meta.evidence == 'positive-control'
                else:
                    matches = (case.kind == 'valid' and member['phase'] == 'run'
                               and case.meta.evidence == 'effect')
                if not matches:
                    raise SuiteError(f"{link['id']}: role does not match canonical case {case.name}")
                if case.meta.oracle_basis != 'standard':
                    raise SuiteError(f'{case.name}: a canonical link cannot import an additional diagnostic policy')
            target = link['target']
            covered.setdefault(target['requirement'], {})[target['facet']] = link['id']
        return covered

    def report(self, cases):
        self.validate_cases(cases)
        if not self.links:
            return []
        by_id = {case.name: case for case in cases}
        groups = {}
        for case in cases:
            groups.setdefault(case.review_key, []).append(case.name)
        result = []
        for link in self.links.values():
            sources = sorted(set(link['target']['source_units'] + link['basis']))
            source_material = {anchor: self._source(anchor) for anchor in sources}
            sections = {anchor.partition('#')[0] for anchor in sources}
            source_reviews = {
                section: dict(
                    state=self.registry.catalogue_review_state(section),
                    fingerprint=self.registry.catalogue_fingerprint(section),
                    record={key: value for key, value in self.registry.catalogues[section].items()
                            if key in ('review_state', 'review_fingerprint', 'review_rationale')})
                for section in sorted(sections) if section in self.registry.catalogues}
            blockers = [f'{section}: catalogue source review is {review["state"]}'
                        for section, review in source_reviews.items() if review['state'] != 'reviewed']
            members = []
            for member in link['cases']:
                case = by_id[member['id']]
                fingerprint = case.fingerprint(self.registry)
                review = self.registry.review(case.review_key, fingerprint, groups[case.review_key])
                if not review.approved:
                    blockers.append(f'{case.name}: fixture review is {review.state}')
                elif not ({member['source'], member['primary_rule']} & set(review.sources)):
                    blockers.append(f'{case.name}: fixture review lacks its canonical source')
                if review.state == 'reference-validated' and not any(
                        item['case'] == case.name and qualifying_reference(case, item)
                        for item in review.references):
                    blockers.append(f'{case.name}: no successful reference at the required phase and supported mode')
                members.append(dict(member, kind=case.kind, evidence=case.meta.evidence,
                                    required_standard=case.meta.standard, review_key=case.review_key,
                                    execution_set=sorted(groups[case.review_key]),
                                    fingerprint=fingerprint, review=asdict(review)))
            material = dict(
                standard=self.registry.standard,
                link={key: value for key, value in link.items() if key != 'review'},
                target_requirement=self.registry.definition_material(link['target']['requirement']),
                sources=source_material, source_reviews=source_reviews, cases=members)
            fingerprint = digest({'@canonical-case-link': json.dumps(material, sort_keys=True).encode()})
            record = link.get('review')
            review = Review(fingerprint=fingerprint)
            if record:
                state = record['state'] if record['fingerprint'] == fingerprint else 'stale'
                if state == 'source-reviewed' and blockers:
                    state = 'stale'
                rationale = (record['rationale'] if state != 'stale' else
                             'Link, target/source, canonical inputs, execution set, or reviews changed.')
                review = Review(state, rationale, fingerprint, record['state'], record['sources'])
            result.append(dict(
                id=link['id'], target=link['target'], basis=link['basis'],
                pattern=link.get('pattern', 'diagnostic-control'),
                claim=link['claim'], limitation=link['limitation'],
                state='current' if review.approved else review.state if record else 'draft',
                review=asdict(review), blockers=blockers, source_reviews=source_reviews, cases=members,
                observation_aggregation='not-computed'))
        return result

    def snapshot(self, cases):
        return {link['id']: dict(fingerprint=link['review']['fingerprint'], state=link['state'])
                for link in self.report(cases)}

    def record_review(self, cases, name, state, rationale):
        string(name, 'evidence link ID')
        string(state, 'evidence review state')
        if name not in self.links:
            raise SuiteError(f'unknown evidence link {name}')
        if state not in LINK_REVIEW_STATES:
            raise SuiteError('link review needs a source-review state, not reference validation')
        string(rationale, 'evidence review rationale')
        report = next(link for link in self.report(cases) if link['id'] == name)
        if state == 'source-reviewed' and report['blockers']:
            raise SuiteError('cannot review linked evidence: ' + '; '.join(report['blockers']))
        link = self.links[name]
        link['review'] = dict(state=state, rationale=rationale,
                              sources=sorted(set(link['target']['source_units'] + link['basis'])),
                              fingerprint=report['review']['fingerprint'])
        self._link(link)
        write_json(self.path, self.data)
