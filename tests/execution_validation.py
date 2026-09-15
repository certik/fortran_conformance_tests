"""Validate trace structure and argv against bound declarations and configuration."""
from pathlib import Path, PurePosixPath

from execution_commands import command_plan
from suite_data import SuiteError, fields, string, validate_compiler_header


def require(condition, name, message):
    if not condition:
        raise SuiteError(f'{name}: {message}')


def absolute_path(value, name):
    string(value, name)
    path = PurePosixPath(value)
    require(path.is_absolute() and path.as_posix() == value and '..' not in path.parts,
            name, 'requires a canonical absolute path')
    return Path(value)


def validate_identity(identity):
    fields(identity, ('command', 'family', 'standard', 'version', 'launcher', 'wrapper'),
           ('c_binding_header',), 'aggregate compiler')
    for key in ('command', 'family', 'standard', 'version'):
        string(identity[key], 'aggregate compiler ' + key)
    require(identity['family'] in ('lfortran', 'gfortran', 'flang'),
            identity['command'], 'unknown Fortran compiler family')
    launcher = identity['launcher']
    require(isinstance(launcher, list) and all(isinstance(arg, str) and arg for arg in launcher),
            identity['command'], 'launcher must be an argv list')
    require(identity['wrapper'] in ('', 'opencoarrays'),
            identity['command'], 'unknown compiler wrapper')
    if identity['wrapper'] == 'opencoarrays':
        require(identity['family'] == 'gfortran' and Path(identity['command']).name == 'caf',
                identity['command'], 'OpenCoarrays wrapper does not match the compiler')
    if identity.get('c_binding_header'):
        validate_compiler_header(identity['c_binding_header'], 'aggregate compiler header')


def validate_trace(check, plan, name, success_status=None):
    trace = check.get('trace', [])
    require(isinstance(trace, list), name, 'trace must be a list')
    require(0 < len(trace) <= len(plan), name, 'missing or excessive declared execution trace')
    for index, (actual, expected) in enumerate(zip(trace, plan)):
        fields(actual, ('phase', 'step', 'command', 'returncode', 'timed_out'),
               ('stdout', 'stderr', 'stdout_hex', 'stderr_hex', 'stdin_sha256'), name + ' trace')
        require((actual['phase'], actual['step']) == (expected['phase'], expected['step']),
                name, 'trace does not follow the declared phase/step order')
        command = actual['command']
        require(isinstance(command, list) and all(isinstance(arg, str) and arg for arg in command),
                name, 'trace command must be an argv list')
        require(command == expected['command'], name,
                'trace command does not match declared compiler/configuration/inputs/executable')
        require(actual.get('stdin_sha256') == expected['stdin_sha256'],
                name, 'trace stdin does not match the declared input asset')
        require(type(actual['returncode']) is int and type(actual['timed_out']) is bool,
                name, 'trace status has invalid types')
        if index < len(trace) - 1:
            require(actual['returncode'] == 0 and not actual['timed_out'],
                    name, 'execution continued after a failed or timed-out build')
    if check['outcome'] == 'pass':
        require(len(trace) == len(plan), name, 'success lacks the complete declared execution trace')
        terminal = trace[-1]
        require(not terminal['timed_out'], name, 'successful terminal phase timed out')
        if success_status is None:
            require(0 <= terminal['returncode'] < 128, name, 'successful diagnostic has abnormal compiler status')
        else:
            require(terminal['returncode'] == success_status, name, 'successful terminal phase has wrong status')
    return trace


def context_and_resources(check, name, wants_header):
    context = check.get('execution_context', {})
    fields(context, ('schema_version', 'workspace', 'compiler_resources'), (), name + ' execution context')
    require(type(context['schema_version']) is int and context['schema_version'] == 1,
            name, 'unknown execution-context schema')
    workspace = absolute_path(context['workspace'], name + ' workspace')
    resources = context['compiler_resources']
    require(isinstance(resources, dict), name, 'compiler resources must be an object')
    require(set(resources) <= ({'ISO_Fortran_binding.h'} if wants_header else set()),
            name, 'undeclared compiler resource')
    for resource, value in resources.items():
        path = absolute_path(value, name + ' compiler resource')
        require(path.name == resource and path.parent.parent == workspace
                and path.parent.name.startswith('processor-header-'),
                name, 'processor header is not in its private workspace directory')
    return context


def exact_hashes(check, expected, name):
    hashes = check.get('input_hashes', {})
    require(isinstance(hashes, dict) and hashes == expected,
            name, 'input hashes do not match the exact declared input/resource set')


def validate_profile(profile, profile_name, expected_hashes, identity, source_root):
    require(isinstance(profile, dict), profile_name, 'profile observation must be an object')
    require(profile.get('outcome') in ('pass', 'fail', 'skip', 'error', 'not-run'),
            profile_name, 'unknown profile observation outcome')
    if profile['outcome'] == 'not-run':
        require(set(profile) <= {'outcome', 'note'}, profile_name, 'unrun profile claims execution evidence')
        return
    fields(profile, ('outcome', 'phase'),
           ('note', 'output', 'trace', 'input_hashes', 'compiler_headers', 'execution_context'),
           profile_name + ' profile')
    if profile['outcome'] == 'error' and not profile.get('trace'):
        require(not profile.get('execution_context') and not profile.get('input_hashes')
                and not profile.get('compiler_headers'),
                profile_name, 'unexecuted profile error claims staged inputs')
        return
    context = context_and_resources(profile, profile_name, False)
    require(not profile.get('compiler_headers'), profile_name, 'profile claims an undeclared processor header')
    exact_hashes(profile, expected_hashes, profile_name)
    plan = command_plan(None, identity, source_root, context, profile=profile_name)
    trace = validate_trace(profile, plan, profile_name, 0)
    if profile['outcome'] == 'pass':
        require(profile.get('phase') == 'profile', profile_name, 'successful profile has wrong observed phase')
    if profile['outcome'] == 'skip':
        require(len(trace) == 2 and trace[-1]['returncode'] == 77 and not trace[-1]['timed_out'],
                profile_name, 'profile unavailability lacks its actual status-77 execution')


def validate_case_trace(member, check, identity, source_root, companion, profiles_blocked):
    name = member['id']
    trace = check.get('trace', [])
    if not trace:
        require(check['outcome'] == 'error' or (
            check['outcome'] in ('fail', 'skip') and profiles_blocked),
            name, 'success or unexplained skip/failure lacks its declared execution trace')
        require(not check.get('execution_context') and not check.get('input_hashes')
                and not check.get('compiler_headers'), name, 'unexecuted case claims staged inputs')
        return False
    require(not profiles_blocked, name, 'case executed after a blocking profile outcome')
    context = context_and_resources(check, name, member['binding_header_required'])
    resources = context['compiler_resources']
    if member['c_companion_required']:
        require(companion is not None, name, 'C compilation/link driver lacks companion identity')
    plan = command_plan(member, identity, source_root, context, companion)
    headers = check.get('compiler_headers', {})
    require(isinstance(headers, dict) and set(headers) == set(resources),
            name, 'compiler-header claims do not match staged resources')
    hashes = dict(member['input_hashes'])
    if resources:
        header = identity.get('c_binding_header')
        require(bool(header) and headers['ISO_Fortran_binding.h'] == header,
                name, 'staged processor header does not match the compiler identity')
        hashes['@compiler/ISO_Fortran_binding.h'] = header['sha256']
    exact_hashes(check, hashes, name)
    terminal = (member['expected_exit'] if member['expected_phase'] == 'run' else 0)
    trace = validate_trace(check, plan, name, terminal if member['kind'] == 'valid' else None)
    seen_builds = [member['execution_plan']['build'][index]
                   for index in range(min(len(trace), len(member['execution_plan'].get('build', []))))]
    header_used = any(step['fortran_binding_header'] for step in seen_builds)
    require(bool(resources) == header_used, name, 'processor-header evidence has no matching C build step')
    if check['outcome'] == 'pass':
        require(check['phase'] == member['expected_phase'], name, 'successful observation has wrong declared phase')
        if member['metadata']['images'] > 1 and member['expected_phase'] == 'run':
            require(bool(identity['launcher']), name, 'successful multi-image execution has no configured launcher')
    if check['outcome'] == 'skip':
        require(check['phase'] == 'launch' and member['metadata']['images'] > 1
                and not identity['launcher'] and plan[-1]['phase'] == 'run'
                and len(trace) == len(plan) - 1
                and trace[-1]['returncode'] == 0 and not trace[-1]['timed_out'],
                name, 'unexplained case skip is not a completed build awaiting its launcher')
    return any(step['phase'] == 'run' for step in trace)
