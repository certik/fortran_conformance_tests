"""Validated, out-of-band fixture descriptions; no arbitrary shell build commands."""
from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Dict, List, Optional

from suite_data import Metadata, SuiteError, fields, read_json, safe_path, string, strings


@dataclass
class BuildStep:
    id: str
    source: str
    language: str
    output: str
    depends_on: List[str] = field(default_factory=list)
    form: str = 'auto'


@dataclass
class Expectation:
    phase: str
    outcome: str
    step: str = ''
    exit_code: int = 0
    stdout: Optional[List[str]] = None
    stderr: Optional[List[str]] = None
    files: Dict[str, List[str]] = field(default_factory=dict)
    diagnostic: dict = field(default_factory=dict)
    file_matches: Dict[str, str] = field(default_factory=dict)


@dataclass
class Fixture:
    path: Path
    name: str
    rule: str
    meta: Metadata
    files: List[str]
    build: List[BuildStep]
    expectation: Expectation
    link: Optional[dict] = None
    arguments: List[str] = field(default_factory=list)
    stdin_file: str = ''
    oracle_profile: str = ''

    @property
    def root(self):
        return self.path.parent

    @property
    def kind(self):
        return 'invalid' if self.expectation.outcome in ('reject', 'diagnose') else 'valid'

    def inputs(self):
        result = {'fixture.json': self.path.read_bytes()}
        result.update({name: safe_path(self.root, name).read_bytes() for name in self.files})
        return result


def output_options(value, context):
    if value is None:
        return None
    options = [value] if isinstance(value, str) else value
    if not isinstance(options, list) or not options or any(not isinstance(item, str) for item in options):
        raise SuiteError(f'{context}: expected a string or a nonempty list of permitted strings')
    if len(options) != len(set(options)):
        raise SuiteError(f'{context}: duplicate alternatives')
    return options


def validate_nonfatal_diagnostics(value, context):
    if not isinstance(value, list):
        raise SuiteError(f'{context}: expected a list of diagnostic predicates')
    for predicate in value:
        fields(predicate, ('compiler', 'severity', 'contains_any'), (), context)
        compiler = string(predicate['compiler'], context + '.compiler')
        severity = string(predicate['severity'], context + '.severity')
        if compiler not in ('lfortran', 'gfortran', 'flang', 'c'):
            raise SuiteError(f'{context}: unknown compiler family')
        if severity not in ('warning', 'portability'):
            raise SuiteError(f'{context}: expected warning or portability severity')
        for message in strings(predicate['contains_any'], context + '.contains_any', nonempty=True):
            string(message, context + '.contains_any')


def load_fixture(path, profiles):
    path = Path(path).resolve()
    data = read_json(path)
    fields(data, ('schema_version', 'id', 'rule', 'facets', 'files', 'build', 'expect'),
           ('evidence', 'requires', 'profiles', 'images', 'standard', 'reference_warnings',
            'oracle_basis', 'oracle_profile', 'link', 'run'), str(path))
    if data['schema_version'] != 1:
        raise SuiteError(f'{path}: unsupported fixture schema')
    name = string(data['id'], f'{path}.id')
    if not re.fullmatch(r'[A-Za-z0-9_.:-]+', name):
        raise SuiteError(f'{path}: execution ID may not contain whitespace or path separators')
    rule = string(data['rule'], f'{path}.rule')
    if not re.fullmatch(r'(?:[RC]\d+|S\d+(?:\.\d+)+(?:-\d{3})?)', rule):
        raise SuiteError(f'{path}: invalid rule ID')
    evidence = data.get('evidence', 'effect')
    if evidence not in ('effect', 'positive-control', 'context-only'):
        raise SuiteError(f'{path}: invalid evidence')
    requires = strings(data.get('requires', []), f'{path}.requires')
    if set(requires) - {'coarray'}:
        raise SuiteError(f'{path}: unknown execution requirement')
    required_profiles = strings(data.get('profiles', []), f'{path}.profiles')
    if set(required_profiles) - set(profiles):
        raise SuiteError(f'{path}: unknown optional processor profile')
    images = data.get('images', 1)
    if type(images) is not int or images < 1 or (images > 1 and 'coarray' not in requires):
        raise SuiteError(f'{path}: invalid image requirement')
    basis = data.get('oracle_basis', 'standard')
    if basis not in ('standard', 'lfortran-policy', 'processor-profile'):
        raise SuiteError(f'{path}: invalid oracle basis')
    oracle_profile = data.get('oracle_profile', '')
    if basis == 'processor-profile':
        string(oracle_profile, f'{path}.oracle_profile')
    standard = data.get('standard', '')
    if standard not in ('', 'f2018', 'f2023'):
        raise SuiteError(f'{path}: invalid language standard')
    meta = Metadata(strings(data['facets'], f'{path}.facets'), evidence, 'coarray' in requires,
                    required_profiles, images, standard,
                    strings(data.get('reference_warnings', []), f'{path}.reference_warnings'), basis, oracle_profile)
    inputs = strings(data['files'], f'{path}.files', nonempty=True)
    for filename in inputs:
        safe_path(path.parent, filename)
        if filename == path.name:
            raise SuiteError(f'{path}: the manifest is not a source input')
    assets = {item.relative_to(path.parent).as_posix() for item in path.parent.rglob('*') if item.is_file()}
    undeclared = assets - set(inputs) - {path.name, 'README.md'}
    if undeclared:
        raise SuiteError(f'{path}: undeclared fixture assets {sorted(undeclared)}')
    if not isinstance(data['build'], list) or not data['build']:
        raise SuiteError(f'{path}: build steps are required')
    steps, outputs, seen = [], set(), set()
    for item in data['build']:
        fields(item, ('id', 'source', 'language', 'output'), ('depends_on', 'form'), str(path))
        step = BuildStep(**item)
        string(step.id, f'{path}.build.id')
        if not re.fullmatch(r'[A-Za-z][\w-]*', step.id) or step.id in seen:
            raise SuiteError(f'{path}: duplicate or invalid build step')
        if step.source not in inputs or step.language not in ('fortran', 'c'):
            raise SuiteError(f'{path}: invalid compilation input or language')
        if step.form not in ('auto', 'fixed', 'free') or (step.language == 'c' and step.form != 'auto'):
            raise SuiteError(f'{path}: invalid source form')
        safe_path(path.parent, step.output, exists=False)
        if step.output in inputs or step.output in outputs:
            raise SuiteError(f'{path}: build outputs must not overwrite inputs or each other')
        if set(strings(step.depends_on, f'{step.id}.depends_on')) - seen:
            raise SuiteError(f'{path}: dependency must name an earlier build step')
        seen.add(step.id)
        outputs.add(step.output)
        steps.append(step)
    link = data.get('link')
    if link is not None:
        fields(link, ('objects', 'output'), ('driver',), f'{path}.link')
        if set(strings(link['objects'], f'{path}.link.objects', nonempty=True)) - outputs:
            raise SuiteError(f'{path}: linker input is not a declared compilation output')
        if link.get('driver', 'fortran') not in ('fortran', 'c'):
            raise SuiteError(f'{path}: invalid linker driver')
        safe_path(path.parent, link['output'], exists=False)
        if link['output'] in inputs or link['output'] in outputs:
            raise SuiteError(f'{path}: linker output collides with an input or object')
    raw = data['expect']
    fields(raw, ('phase', 'outcome'), ('step', 'exit_code', 'stdout', 'stderr', 'files', 'file_matches', 'diagnostic'), f'{path}.expect')
    expectation = Expectation(
        phase=raw['phase'], outcome=raw['outcome'], step=raw.get('step', ''),
        exit_code=raw.get('exit_code', 0), stdout=output_options(raw.get('stdout'), 'stdout'),
        stderr=output_options(raw.get('stderr'), 'stderr'), diagnostic=raw.get('diagnostic', {}))
    if expectation.phase not in ('compile', 'link', 'run') or expectation.outcome not in ('success', 'reject', 'diagnose'):
        raise SuiteError(f'{path}: invalid expected phase/outcome')
    if expectation.outcome == 'diagnose' and expectation.phase != 'compile':
        raise SuiteError(f'{path}: diagnostic reporting expectations require a compile phase')
    if expectation.phase == 'compile' and expectation.step not in seen:
        raise SuiteError(f'{path}: compile expectations must name a build step')
    if expectation.phase == 'compile' and (expectation.step != steps[-1].id or link is not None):
        raise SuiteError(f'{path}: a compile expectation must end the declared build sequence')
    if expectation.phase in ('link', 'run') and link is None:
        raise SuiteError(f'{path}: a link step is required')
    if expectation.phase == 'run' and expectation.outcome != 'success':
        raise SuiteError(f'{path}: runtime outcomes use an exact exit code, not generic rejection')
    if type(expectation.exit_code) is not int or not 0 <= expectation.exit_code <= 255:
        raise SuiteError(f'{path}: expected exit code must be in 0..255')
    if expectation.exit_code and (expectation.phase != 'run' or basis == 'standard'):
        raise SuiteError(f'{path}: nonzero termination needs an explicit policy/profile basis')
    if expectation.outcome in ('reject', 'diagnose'):
        if expectation.outcome == 'diagnose':
            fields(expectation.diagnostic, ('file', 'line'), ('contains_any', 'allow_nonfatal'),
                   f'{path}.diagnostic')
            validate_nonfatal_diagnostics(expectation.diagnostic.get('allow_nonfatal', []),
                                          f'{path}.diagnostic.allow_nonfatal')
        else:
            fields(expectation.diagnostic, () if expectation.phase == 'link' else ('file',),
                   ('line', 'anchor', 'contains_any', 'file') if expectation.phase == 'link'
                   else ('line', 'anchor', 'contains_any'), f'{path}.diagnostic')
        diagnostic_file = expectation.diagnostic.get('file')
        if 'file' in expectation.diagnostic:
            string(diagnostic_file, f'{path}.diagnostic.file')
        if diagnostic_file and diagnostic_file not in set(inputs) | outputs:
            raise SuiteError(f'{path}: diagnostic file is not a declared input')
        if expectation.outcome == 'diagnose' and diagnostic_file not in inputs:
            raise SuiteError(f'{path}: a reporting diagnostic must name a declared input')
        line = expectation.diagnostic.get('line')
        anchor = expectation.diagnostic.get('anchor', '')
        if line is not None and (type(line) is not int or line < 1):
            raise SuiteError(f'{path}: invalid diagnostic line')
        if line is None and anchor not in ('file', 'eof') and expectation.phase != 'link':
            raise SuiteError(f'{path}: a diagnostic line or external anchor is required')
        messages = strings(expectation.diagnostic.get('contains_any', []), 'diagnostic.contains_any')
        for message in messages:
            string(message, 'diagnostic.contains_any')
        if (anchor == 'eof' or expectation.phase == 'link') and not messages:
            raise SuiteError(f'{path}: an EOF expectation needs a diagnostic predicate')
    run = data.get('run', {})
    fields(run, (), ('arguments', 'stdin_file'), f'{path}.run')
    if run and expectation.phase != 'run':
        raise SuiteError(f'{path}: runtime input requires a run expectation')
    arguments = run.get('arguments', [])
    if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
        raise SuiteError(f'{path}: arguments must be strings')
    stdin_file = run.get('stdin_file', '')
    if stdin_file and stdin_file not in inputs:
        raise SuiteError(f'{path}: stdin file is not a declared input')
    file_expectations = raw.get('files', {})
    if not isinstance(file_expectations, dict):
        raise SuiteError(f'{path}: output-file expectations must be an object')
    for filename, expected in file_expectations.items():
        safe_path(path.parent, filename, exists=False)
        if filename in inputs or filename in outputs or (link and filename == link['output']):
            raise SuiteError(f'{path}: output oracle collides with an input or build artifact')
        options = output_options(expected, filename)
        if options is None:
            raise SuiteError(f'{path}: an output-file oracle may not be null')
        expectation.files[filename] = options
    matches = raw.get('file_matches', {})
    if not isinstance(matches, dict):
        raise SuiteError(f'{path}: binary output oracles must be an object')
    for filename, expected_file in matches.items():
        safe_path(path.parent, filename, exists=False)
        if expected_file not in inputs:
            raise SuiteError(f'{path}: binary oracle must name a declared input')
        if filename in inputs or filename in outputs or (link and filename == link['output']):
            raise SuiteError(f'{path}: binary output oracle collides with an input or build artifact')
        expectation.file_matches[filename] = expected_file
    if expectation.phase != 'run' and (expectation.stdout is not None or expectation.stderr is not None or expectation.files
                                       or expectation.file_matches):
        raise SuiteError(f'{path}: runtime output oracles require a run expectation')
    return Fixture(path, name, rule, meta, inputs, steps, expectation, link,
                   arguments, stdin_file, oracle_profile)
