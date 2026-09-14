"""Generic requirement catalogues, source accounting, and fixture adjudication."""
import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import textwrap
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[1]
APPROVED = {'source-reviewed', 'reference-validated'}
REVIEW_STATES = APPROVED | {'unreviewed', 'disputed', 'needs-oracle'}
CATEGORIES = {'effect': 'Effect', 'restriction': 'Restriction',
              'undefined-result': 'Undefined result', 'syntax': 'Syntax'}


class SuiteError(Exception):
    pass


@dataclass
class Metadata:
    facets: List[str] = field(default_factory=list)
    evidence: str = 'effect'
    coarray: bool = False
    profiles: List[str] = field(default_factory=list)
    images: int = 1
    standard: str = ''
    reference_warnings: List[str] = field(default_factory=list)
    oracle_basis: str = 'standard'
    oracle_profile: str = ''


@dataclass
class Review:
    state: str = 'unreviewed'
    rationale: str = 'No adjudication record.'
    fingerprint: str = ''
    recorded_state: str = ''
    sources: List[str] = field(default_factory=list)
    references: List[dict] = field(default_factory=list)

    @property
    def approved(self):
        return self.state in APPROVED


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SuiteError(f'{path}: cannot read JSON: {error}') from error


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def fields(value, required, optional, context):
    if not isinstance(value, dict):
        raise SuiteError(f'{context}: expected an object')
    missing = set(required) - value.keys()
    unknown = value.keys() - set(required) - set(optional)
    if missing or unknown:
        raise SuiteError(f'{context}: missing fields {sorted(missing)}; unknown fields {sorted(unknown)}')


def string(value, context):
    if not isinstance(value, str) or not value.strip():
        raise SuiteError(f'{context}: expected a nonempty string')
    return value


def strings(value, context, nonempty=False):
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise SuiteError(f'{context}: expected a list of strings')
    if len(value) != len(set(value)) or (nonempty and not value):
        raise SuiteError(f'{context}: duplicate or missing entries')
    return value


def safe_path(root, relative, exists=True):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise SuiteError(f'invalid relative path: {relative!r}')
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in ('..', '.') for part in path.parts):
        raise SuiteError(f'path must remain inside its declared root: {relative}')
    root = Path(root).resolve()
    resolved = (root / relative).resolve()
    if resolved == root or root not in resolved.parents:
        raise SuiteError(f'path escapes its declared root: {relative}')
    if exists and not resolved.is_file():
        raise SuiteError(f'missing file: {resolved}')
    return resolved


def digest(parts):
    value = hashlib.sha256()
    for name, data in sorted(parts.items()):
        value.update(name.encode())
        value.update(b'\0')
        value.update(str(len(data)).encode())
        value.update(b'\0')
        value.update(data)
    return value.hexdigest()


def render_requirement(requirement):
    def prose(value):
        return '\n\n'.join(textwrap.fill(paragraph, width=88, break_long_words=False,
                                        break_on_hyphens=False)
                           for paragraph in value.split('\n\n'))

    result = [
        f"### {requirement['id']}: {requirement['title']}",
        f"**Source:** {requirement['source']} **Class:** {CATEGORIES[requirement['category']]}.",
        '**Definition:** ' + prose(requirement['definition']),
        '**Diagnostic obligation:** ' + requirement['diagnostic_obligation'] + '.',
        '**Facets:** ' + ', '.join(f'`{facet}`' for facet in requirement['facets']) + '.',
    ]
    for key, label in (('oracle', 'Oracle'), ('oracle_limitation', 'Oracle limitation'),
                       ('dependencies', 'Dependencies')):
        if requirement.get(key):
            result.append(f'**{label}:** ' + prose(requirement[key]))
    return '\n\n'.join(result) + '\n'


class Registry:
    def __init__(self, root=ROOT, index='doc/catalogues/index.json'):
        self.root = Path(root).resolve()
        self.index = read_json(safe_path(self.root, index))
        fields(self.index, ('schema_version', 'standard', 'source_inventory', 'rule_inventory',
                            'catalogues', 'reviews'), ('legacy_requirements', 'source_inventory_review'), 'catalogue index')
        if self.index['schema_version'] != 1:
            raise SuiteError('unsupported catalogue-index schema')
        self.source = read_json(safe_path(self.root, self.index['source_inventory']))
        self.standard = self.index['standard']
        for key in ('document', 'edition', 'sha256'):
            if self.source.get(key) != self.standard.get(key):
                raise SuiteError(f'catalogue and source inventory disagree on {key}')
        self.sections = self.source['sections']
        source_review = self.index.get('source_inventory_review', {})
        if isinstance(source_review, str):
            source_review = {'state': source_review}
        self.source_review_state = source_review.get('state', 'unreviewed')
        if self.source_review_state == 'reviewed':
            actual = hashlib.sha256(safe_path(self.root, self.index['source_inventory']).read_bytes()).hexdigest()
            if source_review.get('fingerprint') != actual or not source_review.get('rationale'):
                self.source_review_state = 'stale'
        self.numbered = set(re.findall(
            r'^([RC]\d+)\b', safe_path(self.root, self.index['rule_inventory']).read_text(), re.M))
        inventoried = {unit for section in self.sections.values() for unit in section['units']
                       if re.fullmatch(r'[RC]\d+', unit)}
        if self.numbered != inventoried:
            raise SuiteError('numbered-rule inventory differs from the pinned PDF census')
        self.legacy = self.index.get('legacy_requirements', {})
        self.catalogues = {}
        self.catalogue_paths = {}
        self.requirements = {}
        self.requirement_sections = {}
        self.accounting = {}
        for filename in strings(self.index['catalogues'], 'catalogues', nonempty=True):
            catalogue = read_json(safe_path(self.root, filename))
            fields(catalogue, ('schema_version', 'section', 'requirements', 'accounting'),
                   ('subunits', 'render', 'review_state', 'review_fingerprint', 'review_rationale'), filename)
            section = catalogue['section']
            if section not in self.sections or section in self.catalogues:
                raise SuiteError(f'{filename}: unknown or duplicate source section {section}')
            if catalogue['schema_version'] != 1:
                raise SuiteError(f'{filename}: unsupported schema')
            if catalogue.get('review_state', 'draft') not in ('draft', 'reviewed'):
                raise SuiteError(f'{filename}: invalid catalogue review state')
            self.catalogues[section] = catalogue
            self.catalogue_paths[section] = safe_path(self.root, filename)
            for requirement in catalogue['requirements']:
                self._requirement(requirement, section)
        for section, catalogue in self.catalogues.items():
            self._accounting(section, catalogue)
        reviews_path = safe_path(self.root, self.index['reviews'], exists=False)
        self.reviews_path = reviews_path
        review_data = read_json(reviews_path) if reviews_path.exists() else {'schema_version': 1, 'fixtures': {}}
        fields(review_data, ('schema_version', 'fixtures'), (), 'reviews')
        if review_data['schema_version'] != 1:
            raise SuiteError('unsupported review schema')
        self.reviews = review_data['fixtures']
        for name, review in self.reviews.items():
            self._review_record(name, review)

    def _requirement(self, requirement, section):
        fields(requirement, ('id', 'title', 'source', 'source_units', 'category', 'diagnostic_obligation',
                             'definition', 'facets', 'pending'),
               ('oracle', 'oracle_limitation', 'dependencies'), f'requirement in {section}')
        name = requirement['id']
        if name not in self.numbered and not re.fullmatch(re.escape('S' + section + '-') + r'\d{3}', name):
            raise SuiteError(f'{name}: unknown numbered rule or S ID inconsistent with {section}')
        if name in self.requirements:
            raise SuiteError(f'duplicate requirement {name}')
        for key in ('title', 'source', 'definition'):
            string(requirement[key], f'{name}.{key}')
        strings(requirement['source_units'], f'{name}.source_units', nonempty=True)
        if requirement['category'] not in CATEGORIES:
            raise SuiteError(f'{name}: unknown category')
        if requirement['diagnostic_obligation'] not in ('required', 'not-required', 'context-dependent'):
            raise SuiteError(f'{name}: invalid diagnostic obligation')
        facets = strings(requirement['facets'], f'{name}.facets', nonempty=True)
        pending = requirement['pending']
        if not isinstance(pending, dict) or set(pending) - set(facets):
            raise SuiteError(f'{name}: pending entries must name declared facets')
        for facet, reason in pending.items():
            string(reason, f'{name}.pending.{facet}')
        if not requirement.get('oracle') and not requirement.get('oracle_limitation'):
            raise SuiteError(f'{name}: needs an oracle or an explicit oracle limitation')
        self.requirements[name] = requirement
        self.requirement_sections[name] = section

    def _accounting(self, section, catalogue):
        units = set(self.sections[section]['units'])
        for parent, children in catalogue.get('subunits', {}).items():
            if parent not in units:
                raise SuiteError(f'{section}: subdivision has unknown parent {parent}')
            for child in strings(children, f'{section}.{parent}', nonempty=True):
                if child in units or not child.startswith(parent + '.'):
                    raise SuiteError(f'{section}: invalid or duplicate subdivision {child}')
                units.add(child)
        accounting = {}
        for record in catalogue['accounting']:
            fields(record, ('unit', 'disposition'), ('requirements', 'rationale'), f'{section} accounting')
            unit = record['unit']
            if unit not in units or unit in accounting:
                raise SuiteError(f'{section}: unknown or duplicate source unit {unit}')
            disposition = record['disposition']
            if disposition not in ('requirements', 'definition', 'permission', 'recommendation', 'informative',
                                   'structural', 'unresolved'):
                raise SuiteError(f'{section}#{unit}: unknown disposition')
            references = strings(record.get('requirements', []), f'{section}#{unit}.requirements')
            if disposition == 'requirements' and not references:
                raise SuiteError(f'{section}#{unit}: requirement mapping is empty')
            if disposition != 'requirements':
                string(record.get('rationale'), f'{section}#{unit}.rationale')
            for reference in references:
                if reference not in self.requirements and reference not in self.numbered:
                    raise SuiteError(f'{section}#{unit}: unknown requirement {reference}')
            accounting[unit] = record
        if set(accounting) != units:
            raise SuiteError(f'{section}: unclassified source units {sorted(units - set(accounting))}')
        for requirement in catalogue['requirements']:
            for unit in requirement['source_units']:
                if unit not in accounting or requirement['id'] not in accounting[unit].get('requirements', []):
                    raise SuiteError(f"{requirement['id']}: source anchor {unit} is not mapped back to the requirement")
        self.accounting[section] = accounting

    def catalogue_fingerprint(self, section):
        if section not in self.catalogues:
            raise SuiteError(f'unknown catalogue section {section}')
        content = {key: value for key, value in self.catalogues[section].items()
                   if key not in ('review_state', 'review_fingerprint', 'review_rationale')}
        material = dict(standard=self.standard, source_section=self.sections[section], catalogue=content)
        return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()

    def catalogue_review_state(self, section):
        catalogue = self.catalogues[section]
        state = catalogue.get('review_state', 'draft')
        if state == 'reviewed':
            if (catalogue.get('review_fingerprint') != self.catalogue_fingerprint(section)
                    or not isinstance(catalogue.get('review_rationale'), str)
                    or not catalogue['review_rationale'].strip()):
                return 'stale'
        return state

    def record_catalogue_review(self, section, rationale):
        string(rationale, 'catalogue review rationale')
        fingerprint = self.catalogue_fingerprint(section)
        catalogue = self.catalogues[section]
        catalogue.update(review_state='reviewed', review_fingerprint=fingerprint,
                         review_rationale=rationale)
        write_json(self.catalogue_paths[section], catalogue)

    def _review_record(self, name, record):
        fields(record, ('state', 'rationale', 'sources', 'fingerprint'), ('references',), f'review {name}')
        if record['state'] not in REVIEW_STATES:
            raise SuiteError(f'{name}: unknown review state')
        string(record['rationale'], f'{name}.review rationale')
        strings(record['sources'], f'{name}.review sources', nonempty=True)
        for source in record['sources']:
            if source in self.numbered:
                continue
            section, separator, unit = source.partition('#')
            if not separator or section not in self.sections or unit not in (
                    set(self.sections[section]['units']) | set(self.accounting.get(section, {}))):
                raise SuiteError(f'{name}: unknown review source anchor {source}')
        if not re.fullmatch(r'[0-9a-f]{64}', record['fingerprint']):
            raise SuiteError(f'{name}: invalid review fingerprint')
        if record['state'] == 'reference-validated' and not record.get('references'):
            raise SuiteError(f'{name}: reference-validated review has no recorded evidence')
        references = record.get('references', [])
        if not isinstance(references, list):
            raise SuiteError(f'{name}: reference evidence must be a list')
        observed = {}
        for observation in references:
            fields(observation, ('case', 'compiler', 'version', 'standard', 'phase', 'outcome'), (), f'{name} reference')
            for key, value in observation.items():
                string(value, f'{name}.reference.{key}')
            case = observation['case']
            if case != name and not case.startswith(name + ':'):
                raise SuiteError(f'{name}: reference evidence belongs to another fixture')
            if observation['outcome'] not in ('pass', 'fail', 'skip', 'error'):
                raise SuiteError(f'{name}: invalid reference outcome')
            observed.setdefault(case, False)
            observed[case] |= observation['outcome'] == 'pass'
        if record['state'] == 'reference-validated' and not all(observed.values()):
            raise SuiteError(f'{name}: not every recorded case has successful reference evidence')

    def definition_material(self, rule):
        if rule in self.requirements:
            return self.requirements[rule]
        if rule in self.legacy:
            return self.legacy[rule]
        if rule in self.numbered:
            return {'numbered_rule': rule}
        raise SuiteError(f'unknown requirement {rule}')

    def fingerprint(self, rule, inputs):
        parts = dict(inputs)
        parts['@standard'] = json.dumps(self.standard, sort_keys=True).encode()
        parts['@requirement'] = json.dumps(self.definition_material(rule), sort_keys=True).encode()
        return digest(parts)

    def review(self, key, fingerprint, case_names=None):
        record = self.reviews.get(key)
        if not record:
            return Review(fingerprint=fingerprint)
        state = record['state'] if record['fingerprint'] == fingerprint else 'stale'
        if state == 'reference-validated' and case_names is not None:
            observed = {item['case'] for item in record['references']}
            if observed != set(case_names):
                raise SuiteError(f'{key}: reference approval does not cover the current execution set')
        rationale = record['rationale'] if state != 'stale' else 'Fixture, profile, or requirement changed after review.'
        return Review(state, rationale, fingerprint, record['state'],
                      record['sources'], record.get('references', []))

    def record_review(self, key, fingerprint, state, rationale, sources, references=None):
        record = dict(state=state, rationale=rationale, sources=sources, fingerprint=fingerprint)
        if references:
            record['references'] = references
        self._review_record(key, record)
        self.reviews[key] = record
        write_json(self.reviews_path, {'schema_version': 1, 'fixtures': dict(sorted(self.reviews.items()))})

    def validate_cases(self, cases):
        covered = {name: set() for name in self.requirements}
        identifiers = set()
        for case in cases:
            if case.name in identifiers:
                raise SuiteError(f'duplicate execution ID {case.name}')
            identifiers.add(case.name)
            self.definition_material(case.rule)
            requirement = self.requirements.get(case.rule)
            if not requirement:
                continue
            facets = case.meta.facets
            if not facets or len(facets) != len(set(facets)) or set(facets) - set(requirement['facets']):
                raise SuiteError(f'{case.name}: missing, duplicate, or unknown catalogue facets')
            if case.kind == 'valid':
                allowed = ({'effect', 'positive-control'} if case.rule in self.numbered else {
                    'effect': {'effect'}, 'restriction': {'positive-control'},
                    'undefined-result': {'context-only'}, 'syntax': {'positive-control'},
                }[requirement['category']])
                if case.meta.evidence not in allowed:
                    raise SuiteError(f'{case.name}: requires {" or ".join(sorted(allowed))} evidence')
            elif requirement['category'] == 'undefined-result':
                raise SuiteError(f'{case.name}: an undefined value is not a rejection oracle')
            elif requirement['diagnostic_obligation'] != 'required' and case.meta.oracle_basis != 'lfortran-policy':
                raise SuiteError(f'{case.name}: a prose rejection case needs an explicit diagnostic-policy basis')
            covered[case.rule].update(facets)
        for name, requirement in self.requirements.items():
            missing = set(requirement['facets']) - covered[name]
            if missing != set(requirement['pending']):
                raise SuiteError(f'{name}: uncovered facets {sorted(missing)} differ from declared pending facets')
        return covered

    def audit(self, cases):
        covered = self.validate_cases(cases)
        total = accounted = unresolved = 0
        sections_without_catalogues = []
        for section, entry in self.sections.items():
            records = self.accounting.get(section, {})
            if entry['units'] and section not in self.catalogues:
                sections_without_catalogues.append(section)
            for unit, data in entry['units'].items():
                total += 1
                if unit in records:
                    if records[unit]['disposition'] == 'unresolved':
                        unresolved += 1
                    else:
                        accounted += 1
                elif data['kind'] == 'numbered-item' and unit in self.numbered:
                    accounted += 1
                else:
                    unresolved += 1
        fine = [(unit, record) for section, records in self.accounting.items()
                for unit, record in records.items() if unit not in self.sections[section]['units']]
        unresolved_fine = sum(record['disposition'] == 'unresolved' for _, record in fine)
        catalogue_reviews = {section: self.catalogue_review_state(section) for section in self.catalogues}
        return dict(
            sections=len(self.sections), base_source_units=total, accounted_base_units=accounted,
            unresolved_base_units=unresolved, detailed_catalogues=len(self.catalogues),
            sections_without_catalogues=sections_without_catalogues,
            requirements=len(self.requirements), authored_facets=sum(map(len, covered.values())),
            pending_facets=sum(len(item['pending']) for item in self.requirements.values()),
            fine_source_units=len(fine), unresolved_fine_units=unresolved_fine,
            source_inventory_review=self.source_review_state,
            catalogue_reviews=catalogue_reviews,
            complete_source=self.source_review_state == 'reviewed' and unresolved == 0
            and unresolved_fine == 0 and not sections_without_catalogues
            and all(state == 'reviewed' for state in catalogue_reviews.values()))

    def render(self, write=False):
        errors = []
        for section, catalogue in self.catalogues.items():
            if 'render' not in catalogue:
                continue
            target = catalogue['render']
            path = safe_path(self.root, target['path'])
            begin = f'<!-- BEGIN GENERATED {section} -->'
            end = f'<!-- END GENERATED {section} -->'
            text = path.read_text()
            if text.count(begin) != 1 or text.count(end) != 1:
                raise SuiteError(f'{path}: missing or duplicate generated-region markers')
            before, rest = text.split(begin)
            old, after = rest.split(end)
            generated = '\n\n' + '\n'.join(render_requirement(item) for item in catalogue['requirements']) + '\n'
            if old != generated:
                if write:
                    path.write_text(before + begin + generated + end + after)
                else:
                    errors.append(str(path.relative_to(self.root)))
        if errors:
            raise SuiteError('generated catalogue views are stale: ' + ', '.join(errors))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    registry = Registry()
    registry.render(write=args.render)
    print(f'Loaded {len(registry.catalogues)} catalogues and {len(registry.requirements)} structured requirements.')


if __name__ == '__main__':
    main()
