"""Finite source-use inventories, without executions or facet-completion credit."""
from collections import Counter
from dataclasses import asdict
import json
import re

from evidence_links import LINK_REVIEW_STATES
from suite_data import (Review, SuiteError, canonical_evidence_path, digest, fields,
                        read_json, string, strings, write_json)


class SourceUses:
    def __init__(self, registry, filename=None):
        self.registry = registry
        self.path = canonical_evidence_path(registry.root, filename) if filename is not None else None
        self.data = read_json(self.path, unique_keys=True) if self.path else {
            'schema_version': 1, 'standard': registry.standard, 'inventories': []}
        fields(self.data, ('schema_version', 'standard', 'inventories'), (), 'source-use registry')
        if type(self.data['schema_version']) is not int or self.data['schema_version'] != 1:
            raise SuiteError('unsupported source-use schema')
        if self.data['standard'] != registry.standard:
            raise SuiteError('source-use registry does not match the pinned standard')
        if not isinstance(self.data['inventories'], list):
            raise SuiteError('source-use inventories must be a list')
        self.inventories = {}
        targets = set()
        for inventory in self.data['inventories']:
            self._validate(inventory)
            target = (inventory['target']['requirement'], inventory['target']['facet'])
            if inventory['id'] in self.inventories or target in targets:
                raise SuiteError('duplicate source-use inventory ID or target')
            self.inventories[inventory['id']] = inventory
            targets.add(target)

    def _universe(self, inventory):
        sections = strings(inventory['sections'], f'{inventory["id"]}.sections', nonempty=True)
        units = {}
        for section in sections:
            entry = self.registry.sections.get(section)
            if entry is None or not entry['units']:
                raise SuiteError(f'{inventory["id"]}: unknown or empty source section {section}')
            for unit in set(entry['units']) | set(self.registry.accounting.get(section, {})):
                anchor = section + '#' + unit
                units[anchor] = self.registry.source_material(anchor)
        return dict(sorted(units.items()))

    def _sources(self, inventory, universe):
        return sorted(set(universe) | set(inventory['target']['source_units']) | set(inventory['basis']))

    def _validate(self, inventory):
        fields(inventory, ('id', 'target', 'basis', 'sections', 'coverage_credit',
                           'claim', 'limitation', 'entries'), ('review',), 'source-use inventory')
        name = string(inventory['id'], 'source-use inventory ID')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]*', name):
            raise SuiteError(f'{name}: invalid source-use inventory ID')
        if inventory['coverage_credit'] != 'none':
            raise SuiteError(f'{name}: source-use inventory cannot grant facet or execution credit')
        target = inventory['target']
        fields(target, ('requirement', 'facet', 'source_units'), (), f'{name}.target')
        rule = string(target['requirement'], f'{name}.target.requirement')
        requirement = self.registry.requirements.get(rule)
        if requirement is None:
            raise SuiteError(f'{name}: source-use target needs a structured requirement')
        facet = string(target['facet'], f'{name}.target.facet')
        if facet not in requirement['pending']:
            raise SuiteError(f'{name}: source-use target facet must remain pending')
        section = self.registry.requirement_sections[rule]
        anchors = {section + '#' + unit for unit in requirement['source_units']}
        sources = strings(target['source_units'], f'{name}.target.source_units', nonempty=True)
        if set(sources) - anchors:
            raise SuiteError(f'{name}: source-use target is not anchored to its requirement')
        basis = strings(inventory['basis'], f'{name}.basis', nonempty=True)
        for anchor in sources + basis:
            self.registry.source_material(anchor)
        for key in ('claim', 'limitation'):
            string(inventory[key], f'{name}.{key}')
        universe = self._universe(inventory)
        if not isinstance(inventory['entries'], list):
            raise SuiteError(f'{name}: source-use entries must be a list')
        seen = set()
        for entry in inventory['entries']:
            fields(entry, ('source', 'disposition', 'rationale', 'occurrences'), (), f'{name}.entry')
            source = string(entry['source'], f'{name}.entry.source')
            if source not in universe or source in seen:
                raise SuiteError(f'{name}: unknown, out-of-scope or duplicate source-use entry {source}')
            seen.add(source)
            disposition = string(entry['disposition'], f'{source}.disposition')
            if disposition not in ('mapped', 'not-applicable', 'pending'):
                raise SuiteError(f'{source}: unknown source-use disposition')
            string(entry['rationale'], f'{source}.rationale')
            occurrences = entry['occurrences']
            if not isinstance(occurrences, list):
                raise SuiteError(f'{source}: occurrences must be a list')
            if disposition == 'mapped' and not occurrences:
                raise SuiteError(f'{source}: mapped entry needs an occurrence')
            if disposition == 'not-applicable' and occurrences:
                raise SuiteError(f'{source}: not-applicable entry cannot contain occurrences')
            identities = set()
            for occurrence in occurrences:
                fields(occurrence, ('term', 'ordinal', 'resolution', 'definition', 'dependencies',
                                    'rationale'), (), f'{source}.occurrence')
                term = string(occurrence['term'], f'{source}.term')
                ordinal = occurrence['ordinal']
                if type(ordinal) is not int or ordinal < 1:
                    raise SuiteError(f'{source}: occurrence ordinal must be a positive integer')
                if (term, ordinal) in identities:
                    raise SuiteError(f'{source}: duplicate term/ordinal occurrence')
                identities.add((term, ordinal))
                resolution = string(occurrence['resolution'], f'{source}.resolution')
                if resolution not in ('target', 'explicit-override'):
                    raise SuiteError(f'{source}: unknown source-use resolution')
                definition = string(occurrence['definition'], f'{source}.definition')
                dependencies = strings(occurrence['dependencies'], f'{source}.dependencies')
                for anchor in [definition, *dependencies]:
                    self.registry.source_material(anchor)
                    if anchor not in set(sources + basis):
                        raise SuiteError(f'{source}: occurrence dependency missing from target/basis: {anchor}')
                if (definition in sources) != (resolution == 'target'):
                    raise SuiteError(f'{source}: resolution disagrees with the target/override definition')
                string(occurrence['rationale'], f'{source}.occurrence.rationale')
        if 'review' in inventory:
            review = inventory['review']
            fields(review, ('state', 'rationale', 'sources', 'fingerprint'), (), f'{name}.review')
            if string(review['state'], f'{name}.review.state') not in LINK_REVIEW_STATES:
                raise SuiteError(f'{name}: source-use review is not compiler reference validation')
            string(review['rationale'], f'{name}.review.rationale')
            fingerprint = string(review['fingerprint'], f'{name}.review.fingerprint')
            if not re.fullmatch(r'[0-9a-f]{64}', fingerprint):
                raise SuiteError(f'{name}: invalid source-use review fingerprint')
            for anchor in strings(review['sources'], f'{name}.review.sources', nonempty=True):
                if not re.fullmatch(r'[^#\s]+#[^#\s]+', anchor):
                    raise SuiteError(f'{name}: invalid historical source-use review anchor')

    def report(self):
        result = []
        for inventory in self.inventories.values():
            self._validate(inventory)
            universe = self._universe(inventory)
            sources = self._sources(inventory, universe)
            sections = {anchor.partition('#')[0] for anchor in sources}
            source_reviews = {
                section: dict(
                    state=self.registry.catalogue_review_state(section),
                    fingerprint=self.registry.catalogue_fingerprint(section),
                    record={key: value for key, value in self.registry.catalogues[section].items()
                            if key in ('review_state', 'review_fingerprint', 'review_rationale')})
                if section in self.registry.catalogues else dict(state='missing')
                for section in sorted(sections)}
            blockers = [f'{section}: catalogue source review is {review["state"]}'
                        for section, review in source_reviews.items() if review['state'] != 'reviewed']
            entries = {entry['source']: entry for entry in inventory['entries']}
            members = []
            for anchor, source in universe.items():
                entry = entries.get(anchor)
                members.append(dict(
                    source=anchor, level='base' if source['unit'] == source['parent'] else 'fine',
                    disposition=entry['disposition'] if entry else 'missing',
                    rationale=entry['rationale'] if entry else 'No source-use classification was supplied.',
                    occurrences=entry['occurrences'] if entry else []))
            material = dict(
                standard=self.registry.standard,
                inventory={key: value for key, value in inventory.items() if key != 'review'},
                target_requirement=self.registry.definition_material(inventory['target']['requirement']),
                sources={anchor: self.registry.source_material(anchor) for anchor in sources},
                source_reviews=source_reviews)
            fingerprint = digest({'@source-use-inventory': json.dumps(material, sort_keys=True).encode()})
            record = inventory.get('review')
            review = Review(fingerprint=fingerprint)
            if record:
                current = record['fingerprint'] == fingerprint and set(record['sources']) == set(sources)
                state = record['state'] if current else 'stale'
                if state == 'source-reviewed' and blockers:
                    state = 'stale'
                rationale = (record['rationale'] if state != 'stale' else
                             'Source-use inventory, source scope, target, dependencies or reviews changed.')
                review = Review(state, rationale, fingerprint, record['state'], record['sources'])
            counts = Counter(member['disposition'] for member in members)
            result.append(dict(
                id=inventory['id'], target=inventory['target'], basis=inventory['basis'],
                sections=inventory['sections'], coverage_credit='none',
                claim=inventory['claim'], limitation=inventory['limitation'],
                state='current' if review.approved else review.state if record else 'draft',
                review=asdict(review), blockers=blockers, source_reviews=source_reviews,
                source_unit_count=len(members),
                base_source_unit_count=sum(member['level'] == 'base' for member in members),
                fine_source_unit_count=sum(member['level'] == 'fine' for member in members),
                disposition_counts={key: counts[key] for key in ('mapped', 'not-applicable', 'pending', 'missing')},
                classified_scope=not counts['pending'] and not counts['missing'],
                occurrence_record_count=sum(len(member['occurrences']) for member in members),
                members=members, facet_completion='pending', universal_conformance='not-established',
                new_executions=0, observation_aggregation='not-applicable'))
        return result

    def snapshot(self):
        return {item['id']: dict(
                    fingerprint=item['review']['fingerprint'], state=item['state'],
                    adjudication_fingerprint=digest({
                        '@source-use-review': json.dumps(
                            self.inventories[item['id']].get('review'), sort_keys=True).encode()}))
                for item in self.report()}

    def record_review(self, name, state, rationale):
        if name not in self.inventories:
            raise SuiteError(f'unknown source-use inventory {name}')
        if state not in LINK_REVIEW_STATES:
            raise SuiteError('source-use review needs source adjudication, not reference validation')
        string(rationale, 'source-use review rationale')
        report = next(item for item in self.report() if item['id'] == name)
        if state == 'source-reviewed' and report['blockers']:
            raise SuiteError('cannot review source-use inventory: ' + '; '.join(report['blockers']))
        inventory = self.inventories[name]
        inventory['review'] = dict(
            state=state, rationale=rationale, fingerprint=report['review']['fingerprint'],
            sources=self._sources(inventory, self._universe(inventory)))
        self._validate(inventory)
        write_json(self.path, self.data)
