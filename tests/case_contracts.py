"""Explicit per-execution contracts for retained legacy source containers."""
from dataclasses import replace
from pathlib import Path

from fixture_support import validate_additional_diagnostic_spans, validate_diagnostic_messages
from suite_data import SuiteError, fields, read_json, strings


def apply_case_contracts(cases, known_profiles, root, fixture_roots=()):
    by_path = {}
    for case in cases:
        if case.isolated is not None:
            by_path.setdefault(case.path, []).append(case)
    expected = {Path(path).with_suffix('.cases.json').resolve() for path in by_path}
    found = {path.resolve() for path in Path(root).glob('**/*.cases.json')
             if not any(folder in path.resolve().parents for folder in fixture_roots)}
    if found - expected:
        raise SuiteError('per-case contract has no retained invalid source: ' + ', '.join(
            str(path) for path in sorted(found - expected)))
    for source_path, members in by_path.items():
        path = Path(source_path).with_suffix('.cases.json')
        if not path.exists():
            continue
        data = read_json(path, unique_keys=True)
        fields(data, ('schema_version', 'cases'), (), str(path))
        if type(data['schema_version']) is not int or data['schema_version'] != 1:
            raise SuiteError(f'{path}: unsupported per-case contract schema')
        contracts = data['cases']
        if not isinstance(contracts, dict) or set(contracts) != {case.isolated[2] for case in members}:
            raise SuiteError(f'{path}: contracts must cover exactly the retained isolated case IDs')
        for case in members:
            name = case.isolated[2]
            contract = contracts[name]
            fields(contract, ('facets', 'outcome', 'diagnostic'), ('profiles',), f'{path}:{name}')
            facets = strings(contract['facets'], f'{case.name}.facets', nonempty=True)
            profiles = strings(contract.get('profiles', case.meta.profiles), f'{case.name}.profiles')
            if set(profiles) - set(known_profiles):
                raise SuiteError(f'{case.name}: unknown per-case processor profile')
            if contract['outcome'] != 'diagnose':
                raise SuiteError(f'{case.name}: per-case contracts currently require compile-phase diagnose')
            diagnostic = dict(contract['diagnostic']) if isinstance(contract['diagnostic'], dict) else None
            fields(diagnostic, (), ('contains_any', 'equals_any', 'excludes_any', 'line', 'end_line', 'additional_spans'),
                   f'{case.name}.diagnostic')
            validate_diagnostic_messages(diagnostic, f'{case.name}.diagnostic', required=True)
            if 'excludes_any' in diagnostic:
                strings(diagnostic['excludes_any'], f'{case.name}.excludes_any', nonempty=True)
            marker = case.isolated[0]
            first = diagnostic.get('line', marker)
            last = diagnostic.get('end_line', first)
            if (type(first) is not int or type(last) is not int or not 1 <= first <= marker <= last
                    or last > len(case.isolated[-1].splitlines())):
                raise SuiteError(f'{case.name}: per-case diagnostic span must contain its original marker')
            diagnostic.update(file=Path(source_path).name, line=first)
            validate_additional_diagnostic_spans(
                diagnostic, f'{case.name}.diagnostic', len(case.isolated[-1].splitlines()) + 1)
            case.meta = replace(case.meta, facets=list(facets), profiles=list(profiles))
            case.review_key = case.name
            case.contract = dict(schema_version=1, outcome='diagnose', diagnostic=diagnostic)
