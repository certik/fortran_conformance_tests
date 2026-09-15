"""Shared command construction and declared execution plans; never a shell."""
import copy
from dataclasses import asdict
from pathlib import Path

from suite_data import Metadata, SuiteError, safe_path, string


def compiler_flags(identity, meta, path, form='auto'):
    fixed = form == 'fixed' or (form == 'auto' and str(path).endswith('.f'))
    family = identity['family']
    if family == 'lfortran':
        flags = ['--std=' + identity['standard'], '--no-color']
        if fixed:
            flags.append('--fixed-form')
        if meta['coarray']:
            flags.append('--coarray')
    else:
        flags = ['-std=' + identity['standard']]
        if family == 'gfortran':
            flags.append('-fdiagnostics-color=never')
        if fixed:
            flags.append('-ffixed-form')
        elif form == 'free':
            flags.append('-ffree-form')
        if meta['coarray']:
            if family == 'flang':
                flags.append('-fcoarray')
            elif identity.get('wrapper', '') != 'opencoarrays' and Path(identity['command']).name != 'caf':
                flags.append('-fcoarray=lib' if identity.get('launcher') else '-fcoarray=single')
    return flags


def launch_argv(identity, meta, executable, arguments=()):
    command = [executable]
    if meta['coarray'] and identity.get('launcher'):
        command = [token.replace('{images}', str(meta['images'])).replace('{exe}', executable)
                   for token in identity['launcher']]
        if not any('{exe}' in token for token in identity['launcher']):
            command.append(executable)
    return command + list(arguments)


def ordinary_command(identity, meta, source, output):
    return [identity['command']] + compiler_flags(identity, meta, source) + [source, '-o', output]


def syntax_command(identity, meta, source):
    flags = compiler_flags(identity, meta, source)
    flags += (['--semantics-only', '--error-format', 'short']
              if identity['family'] == 'lfortran' else ['-fsyntax-only'])
    return [identity['command']] + flags + [source]


def compile_command(identity, meta, source, output, language, form='auto', cc=None, header_directory=None):
    if language == 'fortran':
        flags = compiler_flags(identity, meta, source, form)
        if identity['family'] == 'lfortran':
            flags += ['--separate-compilation', '--error-format', 'short']
        return [identity['command']] + flags + ['-c', source, '-o', output]
    string(cc, 'C companion command')
    flags = ['-I', header_directory] if header_directory is not None else []
    return [cc, '-std=c11'] + flags + ['-c', source, '-o', output]


def link_command(identity, meta, objects, output, driver='fortran', cc=None):
    if driver == 'fortran':
        return [identity['command']] + compiler_flags(identity, meta, 'link.f90') + objects + ['-o', output]
    string(cc, 'C link driver')
    return [cc] + objects + ['-o', output]


def execution_context(workspace, compiler_resources=None):
    return dict(schema_version=1, workspace=str(Path(workspace).resolve()),
                compiler_resources={name: str(Path(path).resolve())
                                    for name, path in (compiler_resources or {}).items()})


def case_plan(case):
    if case.fixture:
        return dict(schema_version=1, kind='fixture', build=[asdict(step) for step in case.fixture.build],
                    link=copy.deepcopy(case.fixture.link), arguments=list(case.fixture.arguments),
                    stdin_file=case.fixture.stdin_file,
                    expectation=dict(phase=case.fixture.expectation.phase, step=case.fixture.expectation.step,
                                     outcome=case.fixture.expectation.outcome))
    return dict(schema_version=1, kind='ordinary-' + case.kind,
                expectation=dict(phase='run' if case.kind == 'valid' else 'compile',
                                 step='run' if case.kind == 'valid' else 'source',
                                 outcome=('success' if case.kind == 'valid' else
                                          case.contract['outcome'] if case.contract else 'reject')))


def command_plan(member, identity, source_root, context, companion=None, profile=None):
    """Reconstruct argv from bound declarations and the recorded private workspace."""
    workspace = Path(context['workspace'])

    def staged(name):
        return str(safe_path(workspace, name, exists=False))

    def step(phase, name, command, stdin_hash=None):
        return dict(phase=phase, step=name, command=command, stdin_sha256=stdin_hash)

    if profile is not None:
        meta = asdict(Metadata())
        source = str(Path(source_root) / 'tests/profiles' / (profile.replace('-', '_') + '.f90'))
        executable = staged('a.out')
        return [step('profile-compile', profile, ordinary_command(identity, meta, source, executable)),
                step('profile-run', profile, [executable])]
    plan, meta = member['execution_plan'], member['metadata']
    if plan['kind'] == 'ordinary-valid':
        source = str(Path(source_root) / member['path'])
        executable = staged('a.out')
        return [step('compile-link', 'source', ordinary_command(identity, meta, source, executable)),
                step('run', 'run', launch_argv(identity, meta, executable))]
    if plan['kind'] == 'ordinary-invalid':
        source = staged(Path(member['path']).name)
        return [step('compile', 'source', syntax_command(identity, meta, source))]
    if plan['kind'] != 'fixture':
        raise SuiteError('unknown bound execution-plan kind')
    result = []
    cc = companion['command'] if companion else None
    resources = context['compiler_resources']
    for build in plan['build']:
        header_directory = None
        if build['fortran_binding_header']:
            header = resources.get('ISO_Fortran_binding.h')
            if header is not None:
                header_directory = str(Path(header).parent)
        result.append(step('compile', build['id'], compile_command(
            identity, meta, staged(build['source']), staged(build['output']),
            build['language'], build['form'], cc, header_directory)))
    if plan['link']:
        link = plan['link']
        executable = staged(link['output'])
        result.append(step('link', 'link', link_command(
            identity, meta, [staged(name) for name in link['objects']], executable,
            link.get('driver', 'fortran'), cc)))
        if member['expected_phase'] == 'run':
            stdin_hash = member['input_hashes'][plan['stdin_file']] if plan['stdin_file'] else None
            result.append(step('run', 'run', launch_argv(identity, meta, executable, plan['arguments']), stdin_hash))
    return result
