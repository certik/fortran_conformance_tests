"""Content-bound finite execution ledgers, without new cases or coverage credit."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re

from evidence_links import expected_phase, qualifying_reference, LINK_REVIEW_STATES
from execution_commands import case_plan
from execution_validation import absolute_path, require, validate_case_trace, validate_identity, validate_profile
from fixture_support import uses_c_companion
from suite_data import (Review, SuiteError, canonical_evidence_path, case_review_bindings, digest, fields,
                        read_json, safe_path, string, strings, write_json)

CURRENT_ADJUDICATIONS = {'source-reviewed', 'reference-validated', 'needs-oracle', 'disputed'}


def content_fingerprint(value):
    return digest({'@execution-aggregate': json.dumps(value, sort_keys=True).encode()})


def cohort(case):
    if case.kind == 'invalid':
        return 'diagnostic-only'
    if case.meta.evidence != 'effect':
        return case.meta.evidence
    return 'runtime-effect' if expected_phase(case) == 'run' else 'non-runtime-effect'


class ExecutionAggregates:
    def __init__(self, registry, filename=None):
        self.registry = registry
        self.path = canonical_evidence_path(registry.root, filename) if filename is not None else None
        self.data = read_json(self.path, unique_keys=True) if self.path else {
            'schema_version': 1, 'standard': registry.standard, 'aggregates': []}
        fields(self.data, ('schema_version', 'standard', 'aggregates'), (), 'execution aggregates')
        if type(self.data['schema_version']) is not int or self.data['schema_version'] != 1:
            raise SuiteError('unsupported execution-aggregate schema')
        if self.data['standard'] != registry.standard:
            raise SuiteError('execution aggregates do not match the pinned standard')
        if not isinstance(self.data['aggregates'], list):
            raise SuiteError('execution aggregates must be a list')
        self.aggregates = {}
        targets = set()
        for aggregate in self.data['aggregates']:
            self._validate(aggregate)
            name = aggregate['id']
            target = (aggregate['target']['requirement'], aggregate['target']['facet'])
            if name in self.aggregates or target in targets:
                raise SuiteError(f'{name}: duplicate execution aggregate ID or target')
            self.aggregates[name] = aggregate
            targets.add(target)

    def _validate(self, aggregate):
        fields(aggregate, ('id', 'target', 'basis', 'scope', 'coverage_credit', 'claim', 'limitation'),
               ('review',), 'execution aggregate')
        name = string(aggregate['id'], 'execution aggregate ID')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]*', name):
            raise SuiteError(f'{name}: invalid execution aggregate ID')
        if aggregate['scope'] != 'all-collected-cases' or aggregate['coverage_credit'] != 'none':
            raise SuiteError(f'{name}: only observational all-collected-cases aggregation is supported')
        target = aggregate['target']
        fields(target, ('requirement', 'facet', 'source_units'), (), f'{name}.target')
        rule = string(target['requirement'], f'{name}.target.requirement')
        requirement = self.registry.requirements.get(rule)
        if not requirement or rule in self.registry.numbered or requirement['category'] != 'effect':
            raise SuiteError(f'{name}: execution target must be a supplementary effect requirement')
        facet = string(target['facet'], f'{name}.target.facet')
        if facet not in requirement['pending']:
            raise SuiteError(f'{name}: an observational aggregate cannot clear its target pending facet')
        section = self.registry.requirement_sections[rule]
        anchors = {section + '#' + unit for unit in requirement['source_units']}
        sources = strings(target['source_units'], f'{name}.target.source_units', nonempty=True)
        if set(sources) - anchors:
            raise SuiteError(f'{name}: target source is not anchored to its requirement')
        basis = strings(aggregate['basis'], f'{name}.basis', nonempty=True)
        for anchor in sources + basis:
            self.registry.source_material(anchor)
        for key in ('claim', 'limitation'):
            string(aggregate[key], f'{name}.{key}')
        if 'review' in aggregate:
            review = aggregate['review']
            fields(review, ('state', 'rationale', 'sources', 'fingerprint'), (), f'{name}.review')
            self.registry._review_record(name, review)
            if review['state'] not in LINK_REVIEW_STATES:
                raise SuiteError(f'{name}: aggregate adjudication is source review, not reference validation')
            if set(sources + basis) - set(review['sources']):
                raise SuiteError(f'{name}: aggregate review omits declared source anchors')

    def _members(self, cases):
        if len({case.name for case in cases}) != len(cases):
            raise SuiteError('duplicate execution ID in aggregate universe')
        groups, fingerprints = case_review_bindings(cases, self.registry)
        members = []
        for case in sorted(cases, key=lambda item: item.name):
            fingerprint = fingerprints[case.review_key]
            review = self.registry.review(case.review_key, fingerprint, groups[case.review_key])
            if case.fixture:
                inputs = {name: safe_path(case.fixture.root, name).read_bytes() for name in case.fixture.files}
            else:
                raw = (case.isolated[-1].encode('utf-8') if case.isolated
                       else Path(case.path).read_bytes())
                inputs = {Path(case.path).name: raw}
            profiles = {}
            for name in case.meta.profiles:
                path = safe_path(self.registry.root, f'tests/profiles/{name.replace("-", "_")}.f90')
                profiles[name] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}
            members.append(dict(
                id=case.name, primary_rule=case.rule, kind=case.kind,
                path=Path(case.path).resolve().relative_to(self.registry.root).as_posix(),
                cohort=cohort(case), expected_phase=expected_phase(case),
                expected_exit=case.fixture.expectation.exit_code if case.fixture else 0,
                metadata=asdict(case.meta), review_key=case.review_key,
                execution_plan=case_plan(case),
                execution_group=sorted(groups[case.review_key]), fingerprint=fingerprint,
                review=asdict(review),
                input_hashes={name: hashlib.sha256(raw).hexdigest() for name, raw in inputs.items()},
                profile_hashes=profiles,
                c_companion_required=bool(case.fixture and uses_c_companion(case.fixture)),
                binding_header_required=bool(case.fixture and any(
                    step.fortran_binding_header for step in case.fixture.build))))
        return members

    def report(self, cases, include_members=True):
        if not self.aggregates:
            return []
        members = self._members(cases)
        by_id = {case.name: case for case in cases}
        catalogue_context = {
            section: dict(fingerprint=self.registry.catalogue_fingerprint(section),
                          state=self.registry.catalogue_review_state(section))
            for section in sorted(self.registry.catalogues)}
        source_context = dict(
            inventory_fingerprint=content_fingerprint(self.registry.source),
            inventory_review_state=self.registry.source_review_state,
            catalogues=catalogue_context,
            pending_facets=sum(len(item['pending']) for item in self.registry.requirements.values()))
        result = []
        for aggregate in self.aggregates.values():
            self._validate(aggregate)
            sources = sorted(set(aggregate['target']['source_units'] + aggregate['basis']))
            sections = {anchor.partition('#')[0] for anchor in sources}
            source_reviews = {section: catalogue_context[section] for section in sorted(sections)
                              if section in catalogue_context}
            blockers = [f'{section}: catalogue source review is {review["state"]}'
                        for section, review in source_reviews.items() if review['state'] != 'reviewed']
            if not members:
                blockers.append('aggregate universe has no collected cases')
            members_needing_approval = []
            for member in members:
                review = member['review']
                member_issue = None
                if review['state'] not in CURRENT_ADJUDICATIONS:
                    member_issue = f'fixture review is {review["state"]}'
                elif review['state'] == 'reference-validated' and not any(
                        item['case'] == member['id'] and qualifying_reference(by_id[member['id']], item)
                        for item in review['references']):
                    member_issue = 'reference approval lacks a qualified phase/mode'
                if member_issue:
                    blockers.append(f'{member["id"]}: {member_issue}')
                if member_issue or review['state'] not in ('source-reviewed', 'reference-validated'):
                    members_needing_approval.append(dict(
                        id=member['id'], state=review['state'],
                        rationale=member_issue or review['rationale']))
            material = dict(
                standard=self.registry.standard,
                aggregate={key: value for key, value in aggregate.items() if key != 'review'},
                target_requirement=self.registry.definition_material(aggregate['target']['requirement']),
                sources={anchor: self.registry.source_material(anchor) for anchor in sources},
                source_context=source_context, source_reviews=source_reviews, members=members)
            fingerprint = content_fingerprint(material)
            record = aggregate.get('review')
            review = Review(fingerprint=fingerprint)
            if record:
                state = record['state'] if record['fingerprint'] == fingerprint else 'stale'
                if state == 'source-reviewed' and blockers:
                    state = 'stale'
                rationale = (record['rationale'] if state != 'stale' else
                             'Aggregate, source census, current case universe, inputs or reviews changed.')
                review = Review(state, rationale, fingerprint, record['state'], record['sources'])
            item = dict(
                id=aggregate['id'], target=aggregate['target'], basis=aggregate['basis'],
                scope=aggregate['scope'], coverage_credit='none',
                claim=aggregate['claim'], limitation=aggregate['limitation'],
                state='current' if review.approved else review.state if record else 'draft',
                review=asdict(review), blockers=blockers, source_context=source_context,
                source_reviews=source_reviews, member_count=len(members),
                cohort_counts=dict(Counter(member['cohort'] for member in members)),
                member_ids=[member['id'] for member in members],
                all_members_approved=bool(members) and not members_needing_approval,
                members_needing_approval=members_needing_approval,
                facet_completion='pending', universal_conformance='not-established')
            if include_members:
                item['members'] = members
            result.append(item)
        return result

    def snapshot(self, cases):
        return {item['id']: dict(fingerprint=item['review']['fingerprint'], state=item['state'])
                for item in self.report(cases, include_members=False)}

    def record_review(self, cases, name, state, rationale):
        if name not in self.aggregates:
            raise SuiteError(f'unknown execution aggregate {name}')
        if state not in LINK_REVIEW_STATES:
            raise SuiteError('aggregate review needs source adjudication, not reference validation')
        string(rationale, 'execution aggregate review rationale')
        report = next(item for item in self.report(cases) if item['id'] == name)
        if state == 'source-reviewed' and report['blockers']:
            raise SuiteError('cannot review execution aggregate: ' + '; '.join(report['blockers']))
        aggregate = self.aggregates[name]
        aggregate['review'] = dict(
            state=state, rationale=rationale, fingerprint=report['review']['fingerprint'],
            sources=sorted(set(aggregate['target']['source_units'] + aggregate['basis'])))
        self._validate(aggregate)
        write_json(self.path, self.data)


def member_observation(member, row, identity, check, current, provisional, companion, source_root):
    observation = dict(id=member['id'], cohort=member['cohort'], expected_phase=member['expected_phase'],
                       outcome='not-selected', observed_phase=None, qualified_pass=False,
                       runtime_attempted=False, runtime_effect_pass=False, qualification_issues=[])
    if row is None or check is None:
        return observation
    fields(check, ('outcome', 'phase'),
           ('note', 'output', 'trace', 'input_hashes', 'profile_checks', 'compiler_headers', 'execution_context'),
           f'{member["id"]} aggregate check')
    if (row['rule'] != member['primary_rule'] or row['kind'] != member['kind']
            or row['review_key'] != member['review_key'] or row['metadata'] != member['metadata']
            or not isinstance(row['review'], dict)
            or row['review'].get('fingerprint') != member['fingerprint']):
        raise SuiteError(f'{member["id"]}: observation does not match the aggregate input binding')
    if check['outcome'] not in ('pass', 'fail', 'skip', 'error'):
        raise SuiteError(f'{member["id"]}: unknown aggregate observation outcome')
    issues = []
    if not current:
        issues.append('aggregate-not-current')
    if provisional:
        issues.append('provisional-run')
    if member['review']['state'] not in ('source-reviewed', 'reference-validated'):
        issues.append('fixture-not-approved')
    modes = {'f2023', 'f23'} if member['metadata']['standard'] == 'f2023' else {
        'f2018', 'f18', 'f2023', 'f23'}
    if identity['standard'] not in modes:
        issues.append('unsupported-standard-mode')
    profiles = check.get('profile_checks', {})
    for key in ('profile_checks', 'input_hashes', 'compiler_headers'):
        if not isinstance(check.get(key, {}), dict):
            raise SuiteError(f'{member["id"]}: aggregate {key} must be an object')
    if set(profiles) - set(member['profile_hashes']):
        raise SuiteError(f'{member["id"]}: observation includes an undeclared profile')
    profile_outcomes = {}
    profiles_qualified = True
    profiles_blocked = False
    for name, hashes in member['profile_hashes'].items():
        profile = profiles.get(name)
        if profile is not None:
            validate_profile(profile, name, hashes, identity, source_root)
        profile_outcomes[name] = profile['outcome'] if profile is not None else 'not-recorded'
        qualified = profile is not None and profile['outcome'] == 'pass'
        profiles_qualified &= qualified
        profiles_blocked |= profile is not None and profile['outcome'] in ('skip', 'fail', 'error')
        if not qualified:
            issues.append('profile-not-qualified:' + name)
    if check['outcome'] == 'pass' or check.get('trace'):
        require(profiles_qualified, member['id'], 'executed case lacks its successful declared profile evidence')
    runtime_attempted = validate_case_trace(
        member, check, identity, source_root, companion, profiles_blocked)
    qualified = member['kind'] == 'valid' and check['outcome'] == 'pass' and not issues
    observation.update(
        outcome=check['outcome'], observed_phase=check['phase'], note=check.get('note', ''),
        qualified_pass=qualified, runtime_attempted=bool(runtime_attempted),
        runtime_effect_pass=qualified and member['cohort'] == 'runtime-effect',
        qualification_issues=issues, profile_outcomes=profile_outcomes,
        input_hashes=check.get('input_hashes', {}), compiler_headers=check.get('compiler_headers', {}),
        execution_context=check.get('execution_context', {}))
    return observation


def observations(aggregates, results, compilers, reference_only, run_errors=(), companion=None, *, source_root):
    if not aggregates:
        return []
    source_root = absolute_path(str(source_root), 'aggregate source root')
    for row in results:
        fields(row, ('name', 'rule', 'kind', 'check', 'metadata', 'review', 'review_key', 'references'),
               ('status',), 'aggregate result')
        string(row['name'], 'aggregate execution ID')
        if not isinstance(row['references'], dict):
            raise SuiteError('aggregate references must be an object')
    by_id = {row['name']: row for row in results}
    if len(by_id) != len(results):
        raise SuiteError('duplicate execution result in aggregate observations')
    for identity in compilers:
        validate_identity(identity)
    if companion is not None:
        fields(companion, ('command', 'version'), (), 'aggregate C companion')
        for key in ('command', 'version'):
            string(companion[key], 'aggregate C companion ' + key)
    commands = {identity['command'] for identity in compilers}
    if len(commands) != len(compilers):
        raise SuiteError('duplicate compiler identity in aggregate observations')
    targets = [identity['command'] for identity in compilers if identity['family'] == 'lfortran']
    if not reference_only and len(targets) != 1:
        raise SuiteError('execution aggregation requires one explicit target identity')
    target = targets[0] if not reference_only else None
    for row in results:
        if set(row['references']) - (commands - {target}):
            raise SuiteError(f'{row["name"]}: reference observation has no distinct compiler identity')
    output = []
    for aggregate in aggregates:
        member_ids = [member['id'] for member in aggregate['members']]
        if (member_ids != aggregate['member_ids'] or len(set(member_ids)) != len(member_ids)
                or len(member_ids) != aggregate['member_count']):
            raise SuiteError(f'{aggregate["id"]}: inconsistent aggregate universe')
        if set(by_id) - set(aggregate['member_ids']):
            raise SuiteError(f'{aggregate["id"]}: result lies outside the complete aggregate universe')
        projections = []
        for identity in compilers:
            members = []
            for member in aggregate['members']:
                row = by_id.get(member['id'])
                check = (row['check'] if identity['command'] == target else
                         row['references'].get(identity['command'])) if row else None
                members.append(member_observation(
                    member, row, identity, check, aggregate['state'] == 'current',
                    bool(run_errors), companion, source_root))
            cohorts = {}
            for name in sorted({member['cohort'] for member in members}):
                group = [member for member in members if member['cohort'] == name]
                cohorts[name] = dict(
                    population=len(group), outcomes=dict(Counter(member['outcome'] for member in group)),
                    qualified_pass=sum(member['qualified_pass'] for member in group),
                    runtime_attempted=sum(member['runtime_attempted'] for member in group),
                    runtime_effect_pass=sum(member['runtime_effect_pass'] for member in group))
            valid = [member for member in members if member['cohort'] != 'diagnostic-only']
            projections.append(dict(
                compiler=identity, role='target' if identity['command'] == target else 'reference',
                population=len(members), conforming_candidate_population=len(valid), cohorts=cohorts,
                observation_set_complete=bool(members) and all(
                    member['outcome'] != 'not-selected' for member in members),
                valid_observation_set_complete=bool(valid) and all(
                    member['outcome'] != 'not-selected' for member in valid),
                all_declared_valid_expectations_qualified=bool(valid) and all(member['qualified_pass'] for member in valid),
                members=members))
        output.append(dict(aggregate, observations=projections, provisional=bool(run_errors),
                           run_errors=list(run_errors), c_compiler=companion, source_root=str(source_root)))
    return output
