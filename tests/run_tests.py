#!/usr/bin/env python3
"""Run self-checking programs and isolated diagnostic cases.

See tests/README.md for metadata, profiles, case boundaries, and coverage.
Reference results corroborate fixtures; they never determine LFortran's verdict.
"""
import argparse
import collections
import copy
from dataclasses import asdict, dataclass, field, replace
import glob
import json
import hashlib
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Set

from fixture_support import Fixture, load_fixture, uses_c_companion
from case_contracts import apply_case_contracts
from evidence_links import qualifying_reference
from execution_aggregates import observations as execution_observations
from execution_commands import (compiler_flags, compile_command, execution_context,
                                launch_argv, link_command, ordinary_command, syntax_command)
from suite_data import (Metadata, Registry, Review, ROOT, SuiteError, case_review_bindings,
                        safe_path, validate_compiler_header)

HERE = os.path.dirname(os.path.abspath(__file__))
RULE = r'(?:[RC]\d+|S\d+(?:\.\d+)+(?:-\d{3})?)'
MARK = re.compile(r'!\s*\{error\s+(' + RULE + r')(?:\s+([\w-]+))?\}')
NAME = re.compile(r'^([RC]\d+|S[\d_]+)_(valid|invalid)(?:__([a-z][\w-]*))?\.f(90)?$')
SHORT = re.compile(
    r'^(.*?):(\d+)-(\d+):(\d+)-(\d+): ([\w-]+(?:[ \t]+[\w-]+)*[ \t]+(?:error|warning))'
    r'(?: \[([\w.-]+)\])?(?: \(F2023 ([^)]+)\))?: (.*)$', re.I)
REF_LOC = re.compile(r'^(.*?\.(?:f90|f|c|h)):(\d+):(\d+)(?:-(\d+))?(?::|\s|$)')
DECLARED_REF_LOC = re.compile(r'^(.*?):(\d+):(\d+)(?:-(\d+))?(?::|\s|$)')
REF_LOC_HEADER = re.compile(r'^(.*?):(\d+(?:-\d+)?):')
REF_SOURCE_RECORD = re.compile(r'^\s*(?:\d+\s*)?\|(?:\s|$)')
REF_MESSAGE = re.compile(r'^(Error|Fatal Error|Warning|portability):\s*(.*)', re.I)
CONTENT_MESSAGE = re.compile(
    r'^(?:[\w.+-]+:[ \t]*)?(?:[\w-]+[ \t]+)*(?:error|warning|note|remark|help|portability)'
    r'(?: \[[\w.-]+\])?(?: \(F2023 [^)]+\))?:', re.I)
REF_INTERNAL_ERROR = re.compile(r'^(?:fatal\s+)?error:\s*Internal:\s*\S', re.I)
REF_QUOTED_CONTENT = re.compile(r"""(?<!\w)(?:'[^']*'|"[^"]*")(?!\w)""")
INCLUDE_CONTEXT = re.compile(
    r'^\s*(?:In file included from\b|from\s+.+:\d+(?::\d+)?[:,]?\s*$)', re.I)
GNU_DRIVER_MESSAGE = re.compile(r'^f951:\s*(?:Fatal\s+)?(?:Error|Warning):', re.I)
GNU_DRIVER_LINE = re.compile(r'^f951:\s*Warning:\s*(.*?)\s+in line ([1-9]\d*)\s*$', re.I)
HEADER = re.compile(r'^!\s*(rule|covers|evidence|requires|profile|images|standard|reference-warnings|oracle-basis|oracle-profile):\s*(.*?)\s*$')
CASE = re.compile(r'^!\s*case:\s*([\w-]+)\s*$')
ICE = re.compile(r'internal compiler error|LCOMPILERS_ASSERT|assertion .*failed|'
                 r'LLVM ERROR|segmentation fault|PLEASE submit a bug report', re.I)
RESOURCE_FAILURE = re.compile(
    r'^(?:(?:f951|gfortran|flang|lfortran):\s*)?(?:(?:fatal\s+)?error:\s*)?'
    r'(?:out of memory|virtual memory exhausted|cannot allocate memory|'
    r'killed signal terminated program)\b', re.I | re.M)
PROFILES = {path.stem.replace('_', '-') for path in (Path(HERE) / 'profiles').glob('*.f90')}


@dataclass
class ProcessResult:
    returncode: int
    output: str
    timed_out: bool = False
    stdout: str = ''
    stderr: str = ''
    stdout_bytes: Optional[bytes] = None
    stderr_bytes: Optional[bytes] = None


@dataclass
class Diagnostic:
    first: int
    last: int
    codes: Set[str]
    message: str
    file: str = ''
    severity: str = 'error'
    attribution: str = 'located'


@dataclass
class Check:
    outcome: str
    note: str = ''
    phase: str = ''
    output: str = ''
    trace: List[dict] = field(default_factory=list)
    input_hashes: Dict[str, str] = field(default_factory=dict)
    profile_checks: Dict[str, dict] = field(default_factory=dict)
    compiler_headers: Dict[str, dict] = field(default_factory=dict)
    execution_context: dict = field(default_factory=dict)


@dataclass
class SuiteCase:
    name: str
    rule: str
    kind: str
    path: str
    meta: Metadata
    review_key: str
    fixture: Optional[Fixture] = None
    isolated: Optional[tuple] = None
    contract: Optional[dict] = None

    def fingerprint(self, registry):
        if self.fixture:
            inputs = self.fixture.inputs()
        else:
            inputs = {os.path.basename(self.path): Path(self.path).read_bytes()}
        inputs['@metadata'] = json.dumps(asdict(self.meta), sort_keys=True).encode()
        if self.contract is not None:
            inputs['@case-contract'] = json.dumps(self.contract, sort_keys=True).encode()
        for name in self.meta.profiles:
            profile = Path(HERE) / 'profiles' / (name.replace('-', '_') + '.f90')
            inputs['@profile/' + name] = profile.read_bytes()
        return registry.fingerprint(self.rule, inputs)


@dataclass
class Compiler:
    command: str
    family: str
    standard: str
    version: str = ''
    launcher: List[str] = field(default_factory=list)
    profiles: Dict[str, Check] = field(default_factory=dict)
    wrapper: str = ''
    c_binding_header: dict = field(default_factory=dict)

    def configuration(self):
        return dict(command=self.command, family=self.family, standard=self.standard,
                    launcher=self.launcher, wrapper=self.wrapper)

    def flags(self, path, meta, form='auto'):
        return compiler_flags(self.configuration(), asdict(meta), path, form)


def canonical_rule(name):
    if not name.startswith('S'):
        return name
    parts = name[1:].split('_')
    if len(parts[-1]) == 3:
        return 'S' + '.'.join(parts[:-1]) + '-' + parts[-1]
    return 'S' + '.'.join(parts)


def discover(root, patterns=None, allow_empty=False):
    if isinstance(patterns, str):
        patterns = [patterns]
    tests = []
    matched = set()
    for path in sorted(glob.glob(os.path.join(root, '**', '*.f*'), recursive=True)):
        m = NAME.match(os.path.basename(path))
        if not m:
            continue
        rule = canonical_rule(m.group(1))
        matches = {p for p in patterns or [] if p in os.path.basename(path) or p in rule}
        if patterns and not matches:
            continue
        matched.update(matches)
        tests.append((os.path.abspath(path), rule, m.group(2)))
    missing = set(patterns or []) - matched
    if missing:
        raise SuiteError('no tests match: ' + ', '.join(sorted(missing)))
    if not tests and not allow_empty:
        raise SuiteError('no tests discovered in ' + root)
    return tests


def collect_cases(root, registry, patterns=None):
    manifests = sorted(Path(root).glob('**/fixture.json'))
    fixture_roots = {path.parent.resolve() for path in manifests}
    cases_found = []
    for path, rule, kind in discover(root, allow_empty=True):
        if any(folder in Path(path).parents for folder in fixture_roots):
            continue
        meta = metadata(path, rule)
        if rule in registry.legacy:
            meta.oracle_basis = registry.legacy[rule].get('oracle_basis', 'standard')
        base = Path(path).stem
        if kind == 'invalid':
            for item in isolated_cases(path, rule):
                cases_found.append(SuiteCase(f'{base}:{item[2]}', rule, kind, path, meta, base, isolated=item))
        else:
            cases_found.append(SuiteCase(base, rule, kind, path, meta, base))
    for manifest in manifests:
        fixture = load_fixture(manifest, PROFILES)
        cases_found.append(SuiteCase(fixture.name, fixture.rule, fixture.kind, str(manifest),
                                    fixture.meta, fixture.name, fixture=fixture))
    cases_found.sort(key=lambda case: case.name)
    apply_case_contracts(cases_found, PROFILES, root, fixture_roots)
    registry.validate_cases(cases_found)
    case_review_bindings(cases_found, registry)
    return select_cases(cases_found, patterns)


def select_cases(cases_found, patterns):
    if not patterns:
        return cases_found
    if isinstance(patterns, str):
        patterns = [patterns]
    selected, matched = [], set()
    for case in cases_found:
        matching = {pattern for pattern in patterns
                    if pattern in case.name or pattern in case.rule or pattern in case.path}
        if matching:
            selected.append(case)
            matched.update(matching)
    if set(patterns) != matched:
        raise SuiteError('no tests match: ' + ', '.join(sorted(set(patterns) - matched)))
    return selected


def metadata(path, rule):
    values = {}
    for line in Path(path).read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('!'):
            break
        match = HEADER.match(line)
        if match:
            key, value = match.groups()
            if key in values:
                raise SuiteError(f'{path}: duplicate {key} header')
            values[key] = value
    if values.get('rule', rule) != rule:
        raise SuiteError(f'{path}: rule header does not match {rule}')
    if re.fullmatch(r'S[\d.]+-\d{3}', rule):
        if values.get('rule') != rule or not values.get('covers'):
            raise SuiteError(f'{path}: catalogue cases need rule and covers headers')
    evidence = values.get('evidence', 'effect')
    if evidence not in ('effect', 'positive-control', 'context-only'):
        raise SuiteError(f'{path}: invalid evidence {evidence}')
    requires = values.get('requires', '').split()
    if set(requires) - {'coarray'}:
        raise SuiteError(f'{path}: unknown requires header')
    profiles = values.get('profile', '').split()
    if set(profiles) - PROFILES:
        raise SuiteError(f'{path}: unknown profile')
    try:
        images = int(values.get('images', '1'))
    except ValueError as error:
        raise SuiteError(f'{path}: images must be a positive integer') from error
    if images < 1 or (images > 1 and 'coarray' not in requires):
        raise SuiteError(f'{path}: multiple images require coarray')
    standard = values.get('standard', '')
    if standard not in ('', 'f2018', 'f2023'):
        raise SuiteError(f'{path}: unsupported standard header {standard}')
    warnings = values.get('reference-warnings', '').split()
    if any(not re.fullmatch(r'[a-z][a-z0-9-]*', warning) for warning in warnings):
        raise SuiteError(f'{path}: invalid reference warning code')
    basis = values.get('oracle-basis', 'standard')
    if basis not in ('standard', 'lfortran-policy', 'processor-profile'):
        raise SuiteError(f'{path}: invalid oracle basis')
    oracle_profile = values.get('oracle-profile', '')
    if basis == 'processor-profile' and not oracle_profile:
        raise SuiteError(f'{path}: a processor-profile oracle needs a named profile')
    return Metadata(values.get('covers', '').split(), evidence,
                    'coarray' in requires, profiles, images, standard, warnings, basis, oracle_profile)


def run(cmd, cwd, timeout=30, stdin=None):
    try:
        process = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
    except OSError as error:
        raise SuiteError(f'cannot start {cmd[0]}: {error}') from error
    timed_out = False
    try:
        input_bytes = stdin.encode('utf-8') if isinstance(stdin, str) else stdin
        stdout, stderr = process.communicate(input=input_bytes, timeout=timeout)
    except subprocess.TimeoutExpired as initial_timeout:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        cleanup_timeout = min(timeout, 1.0)
        try:
            stdout, stderr = process.communicate(timeout=cleanup_timeout)
        except subprocess.TimeoutExpired as drain_timeout:
            stdout = drain_timeout.output if drain_timeout.output is not None else initial_timeout.output
            stderr = drain_timeout.stderr if drain_timeout.stderr is not None else initial_timeout.stderr
            stdout = b'' if stdout is None else stdout
            stderr = b'' if stderr is None else stderr
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
            try:
                process.wait(timeout=cleanup_timeout)
            except subprocess.TimeoutExpired as error:
                raise SuiteError(f'timed-out subprocess {process.pid} could not be reaped within cleanup bound') from error
    stdout_text = stdout.decode('utf-8', errors='backslashreplace')
    stderr_text = stderr.decode('utf-8', errors='backslashreplace')
    return ProcessResult(process.returncode, stdout_text + stderr_text, timed_out,
                         stdout_text, stderr_text, stdout, stderr)


def failure(result, phase, compiler_process=True):
    if result.timed_out:
        return Check('fail', f'{phase} timed out', phase, result.output)
    if compiler_process and 'ASR verify pass error' in result.output:
        return Check('fail', f'{phase} failed ASR verification', phase, result.output)
    if result.returncode < 0 or (compiler_process and (result.returncode >= 128 or ICE.search(result.output))):
        return Check('fail', f'{phase} crashed (exit {result.returncode})',
                     phase, result.output)
    if compiler_process and native_internal_error(result.output):
        return Check('fail', f'{phase} reported a compiler internal error', phase, result.output)
    if compiler_process and RESOURCE_FAILURE.search(result.output):
        return Check('fail', f'{phase} exhausted compiler resources', phase, result.output)
    return None


def excerpt(output):
    lines = output.strip().splitlines()
    errors = [line for line in lines if re.search(r'error|not yet implemented', line, re.I)]
    return (errors or lines or ['no diagnostic output'])[0][:180]


def compiler(command, is_lfortran, standard, launcher, timeout):
    version = run([command, '--version'], HERE, timeout)
    if version.returncode != 0 or failure(version, 'version query'):
        raise SuiteError(f'{command}: version query failed: {excerpt(version.output)}')
    wrapper = ''
    banner = next((line for line in version.output.splitlines() if line.strip()), '')
    if not banner:
        raise SuiteError(f'{command}: empty compiler version response')
    if is_lfortran:
        family = 'lfortran'
    elif 'OpenCoarrays Coarray Fortran Compiler Wrapper' in version.output:
        show = run([command, '--show'], HERE, timeout)
        if show.returncode or failure(show, 'wrapper query'):
            raise SuiteError(f'{command}: cannot determine the wrapped compiler')
        tokens = shlex.split(show.output)
        if not tokens:
            raise SuiteError(f'{command}: empty wrapped-compiler command')
        underlying = run([tokens[0], '--version'], HERE, timeout)
        if underlying.returncode or failure(underlying, 'wrapped version query') or 'GNU Fortran' not in underlying.output:
            raise SuiteError(f'{command}: wrapper does not identify a working GNU Fortran compiler')
        family, wrapper = 'gfortran', 'opencoarrays'
        banner += '; ' + next(line for line in underlying.output.splitlines() if line.strip())
    elif 'GNU Fortran' in version.output:
        family = 'gfortran'
    elif 'flang' in version.output.lower():
        family = 'flang'
    else:
        raise SuiteError(f'{command}: supported references are GNU Fortran and Flang')
    if standard == 'auto':
        with tempfile.TemporaryDirectory() as tmp:
            source = os.path.join(tmp, 'standard.f90')
            Path(source).write_text('program standard\nimplicit none\nend program\n')
            for candidate in ('f2023', 'f2018'):
                probe = run([command, '-std=' + candidate, '-fsyntax-only', source], tmp, timeout)
                if failure(probe, 'standard probe'):
                    raise SuiteError(f'{command}: standard probe failed: {excerpt(probe.output)}')
                if probe.returncode == 0:
                    standard = candidate
                    break
            else:
                raise SuiteError(f'{command}: neither f2023 nor f2018 mode works')
    return Compiler(command, family, standard, banner, launcher, wrapper=wrapper)


def cases(path):
    out = []
    ids = set()
    for i, line in enumerate(Path(path).read_text().splitlines(), start=1):
        marks = list(MARK.finditer(line))
        if len(marks) > 1:
            raise SuiteError(f'{path}:{i}: only one error marker per line is supported')
        for mark in marks:
            case = mark.group(2) or f'line{i}'
            if case in ids:
                raise SuiteError(f'{path}:{i}: duplicate case ID {case}')
            ids.add(case)
            out.append((i, mark.group(1), case))
    if not out:
        raise SuiteError(f'{path}: invalid file has no error markers')
    return out


def lfortran_diagnostics(output):
    found = []
    for line in output.splitlines():
        m = short_diagnostic_match(line)
        if m:
            first, last = int(m.group(2)), int(m.group(3))
            if first < 1 or last < first:
                continue
            codes = set(re.findall(RULE, m.group(8) or ''))
            if m.group(7):
                codes.add(m.group(7))
            severity = m.group(6).split()[-1].lower()
            found.append(Diagnostic(first, last, codes, m.group(9),
                                    m.group(1), severity))
    return found


def lfortran_errors(output):
    return [diagnostic for diagnostic in lfortran_diagnostics(output)
            if diagnostic.severity == 'error']


def unit_ranges(path):
    ranges, start = [], 1
    for i, line in enumerate(Path(path).read_text().splitlines(), start=1):
        if re.match(r'end\b', line, re.I):
            ranges.append((start, i))
            start = i + 1
    return ranges


def isolated_cases(path, rule):
    """Keep helpers and one case, replacing other cases with blank lines."""
    lines = Path(path).read_text().splitlines(keepends=True)
    markers = cases(path)
    for line, marked_rule, _ in markers:
        if marked_rule != rule:
            raise SuiteError(f'{path}:{line}: marker does not match {rule}')
    starts = [(i, match.group(1)) for i, line in enumerate(lines, 1)
              if (match := CASE.match(line))]
    if starts:
        if len({name for _, name in starts}) != len(starts):
            raise SuiteError(f'{path}: duplicate case boundary')
        if {name for _, name in starts} != {name for _, _, name in markers}:
            raise SuiteError(f'{path}: case boundaries and markers disagree')
        ranges = [(start, starts[i + 1][0] - 1 if i + 1 < len(starts) else len(lines))
                  for i, (start, _) in enumerate(starts)]
    else:
        if path.endswith('.f'):
            raise SuiteError(f'{path}: fixed-form invalid files need explicit ! case: boundaries')
        ranges = unit_ranges(path)
    selected_ranges = {}
    for line, _, case in markers:
        containing = [(lo, hi) for lo, hi in ranges if lo <= line <= hi]
        if len(containing) != 1:
            raise SuiteError(f'{path}:{line}: cannot isolate {case}')
        if containing[0] in selected_ranges.values():
            raise SuiteError(f'{path}:{line}: each case needs its own boundary')
        selected_ranges[case] = containing[0]
        if starts and dict(starts)[containing[0][0]] != case:
            raise SuiteError(f'{path}:{line}: marker is inside a different case')
    for line, marked_rule, case in markers:
        source = lines.copy()
        for other, (lo, hi) in selected_ranges.items():
            if other != case:
                source[lo - 1:hi] = ['\n'] * (hi - lo + 1)
        yield line, marked_rule, case, selected_ranges[case], ''.join(source)


def diagnostic_filename_matches(actual, expected):
    actual, expected = Path(actual), Path(expected)
    if expected.is_absolute():
        return actual == expected
    return bool(expected.parts) and actual.parts[-len(expected.parts):] == expected.parts


def diagnostic_origin_matches(actual, expected, workspace=None):
    if workspace is None:
        return diagnostic_filename_matches(actual, expected)
    try:
        root = Path(workspace)
        if not root.is_absolute():
            return False
        root = root.resolve(strict=True)
        source = safe_path(root, expected).resolve(strict=True)
        origin = Path(actual)
        if not origin.is_absolute():
            origin = root / origin
        return source.is_file() and origin.resolve(strict=True) == source
    except (OSError, RuntimeError, ValueError, SuiteError):
        return False


def reference_location_header(text):
    if REF_SOURCE_RECORD.match(text):
        return None
    if REF_MESSAGE.match(text) or GNU_DRIVER_MESSAGE.match(text) or CONTENT_MESSAGE.match(text):
        text = REF_QUOTED_CONTENT.sub(lambda match: ' ' * len(match.group()), text)
    return REF_LOC_HEADER.match(text)


def reference_location(text, pattern, header):
    location = pattern.match(text)
    if location is None or location.span(2) != header.span(2):
        return None
    if (location.group(4) is not None
            and not 1 <= int(location.group(3)) <= int(location.group(4))):
        return None
    return location


def short_diagnostic_match(text):
    if REF_SOURCE_RECORD.match(text) or INCLUDE_CONTEXT.match(text):
        return None
    header = reference_location_header(text)
    match = SHORT.match(text)
    if header and match and header.span(2) == (match.start(2), match.end(3)):
        return match
    return None


def native_internal_error(output):
    for text in output.splitlines():
        if REF_SOURCE_RECORD.match(text) or INCLUDE_CONTEXT.match(text):
            continue
        header = reference_location_header(text)
        if header:
            short = short_diagnostic_match(text)
            if short:
                severity = short.group(6).split()[-1]
                if REF_INTERNAL_ERROR.match(severity + ': ' + short.group(9)):
                    return True
                continue
            location = reference_location(text, DECLARED_REF_LOC, header)
            if location is None:
                continue
            text = text[location.end():].lstrip()
        if REF_INTERNAL_ERROR.match(text):
            return True
    return False


def reference_diagnostics(output, declared_input=False):
    pending = None
    origin = ''
    for line in output.splitlines():
        if INCLUDE_CONTEXT.match(line):
            pending = None
            origin = ''
            continue
        location = None
        message = line
        header = reference_location_header(line)
        if header:
            pending = None
            origin = ''
            location = reference_location(
                line, DECLARED_REF_LOC if declared_input else REF_LOC, header)
            if location is None:
                continue
            origin = location.group(1)
            pending = int(location.group(2))
            message = line[location.end():].lstrip()
        diagnostic = REF_MESSAGE.match(message)
        if diagnostic:
            if pending is not None:
                yield Diagnostic(pending, pending, set(), diagnostic.group(2),
                                 origin, diagnostic.group(1).lower())
            pending = None
        elif location and message:
            pending = None


def reference_messages(output, filename=None):
    for item in reference_diagnostics(output, declared_input=filename is not None):
        if filename is None or diagnostic_filename_matches(item.file, filename):
            yield item.first, item.severity, item.message


def reference_error_lines(output, filename=None, messages=None):
    return {line for line, severity, message in reference_messages(output, filename)
            if severity in ('error', 'fatal error')
            and (not messages or any(text.lower() in message.lower() for text in messages))}


def reference_warning_lines(output, allowed, filename=None, messages=None):
    return {line for line, severity, message in reference_messages(output, filename)
            if severity in ('warning', 'portability')
            and (not messages or any(text.lower() in message.lower() for text in messages))
            and set(re.findall(r'\[-W([\w-]+)\]', message)).intersection(allowed)}


def profile_check(comp, name, timeout):
    if name in comp.profiles:
        return comp.profiles[name]
    source = os.path.join(HERE, 'profiles', name.replace('-', '_') + '.f90')
    source_hash = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    trace = []
    with tempfile.TemporaryDirectory() as tmp:
        exe = str(safe_path(Path(tmp), 'a.out', exists=False))
        command = ordinary_command(comp.configuration(), asdict(Metadata()), source, exe)
        result = run(command, tmp, timeout)
        trace.append(trace_entry(command, result, 'profile-compile', name))
        check = failure(result, 'profile compilation')
        if check is None and result.returncode != 0:
            check = Check('fail', 'profile does not compile: ' + excerpt(result.output),
                          'profile', result.output)
        if check is None:
            result = run([exe], tmp, timeout)
            trace.append(trace_entry([exe], result, 'profile-run', name))
            check = failure(result, 'profile execution', compiler_process=False)
            if check is None:
                if result.returncode == 77:
                    check = Check('skip', 'profile unavailable: ' + name, 'profile', result.output)
                elif result.returncode != 0:
                    check = Check('fail', 'profile failed: ' + name, 'profile', result.output)
                else:
                    check = Check('pass', phase='profile', output=result.output)
    check.trace = trace
    check.input_hashes = {os.path.basename(source): source_hash}
    check.execution_context = execution_context(tmp)
    comp.profiles[name] = check
    return check


def trace_entry(command, result, phase, step, stdin=None):
    return dict(phase=phase, step=step, command=command, returncode=result.returncode,
                timed_out=result.timed_out, stdout=result.stdout, stderr=result.stderr,
                stdin_sha256=hashlib.sha256(stdin).hexdigest() if stdin is not None else None,
                stdout_hex=result.stdout_bytes.hex() if result.stdout_bytes is not None else None,
                stderr_hex=result.stderr_bytes.hex() if result.stderr_bytes is not None else None)


def check_valid(path, comp, meta, timeout=30):
    for name in meta.profiles:
        check = profile_check(comp, name, timeout)
        if check.outcome != 'pass':
            return check
    with tempfile.TemporaryDirectory() as tmp:
        exe = str(safe_path(Path(tmp), 'a.out', exists=False))
        command = ordinary_command(comp.configuration(), asdict(meta), path, exe)
        result = run(command, tmp, timeout)
        trace = [trace_entry(command, result, 'compile-link', 'source')]
        hashes = {Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest()} if Path(path).is_file() else {}
        def finish(check):
            check.trace, check.input_hashes = trace, hashes
            check.execution_context = execution_context(tmp)
            return check
        failed = failure(result, 'compilation')
        if failed:
            return finish(failed)
        if result.returncode != 0:
            return finish(Check('fail', 'does not compile: ' + excerpt(result.output), 'compile', result.output))
        if meta.images > 1 and not comp.launcher:
            return finish(Check('skip', f'compiled; needs a launcher for {meta.images} images', 'launch'))
        command = launch_command(comp, meta, exe)
        result = run(command, tmp, timeout)
        trace.append(trace_entry(command, result, 'run', 'run'))
        failed = failure(result, 'execution', compiler_process=False)
        if failed:
            return finish(failed)
        if result.returncode != 0:
            return finish(Check('fail', f'runtime exit code {result.returncode}: ' + excerpt(result.output),
                                'run', result.output))
    return finish(Check('pass', phase='run'))


def check_invalid(path, source, line, rule, bounds, comp, meta, codes=False, timeout=30, contract=None):
    with tempfile.TemporaryDirectory() as tmp:
        isolated = str(safe_path(Path(tmp), os.path.basename(path), exists=False))
        Path(isolated).write_text(source)
        command = syntax_command(comp.configuration(), asdict(meta), isolated)
        source_hash = hashlib.sha256(Path(isolated).read_bytes()).hexdigest()
        result = run(command, tmp, timeout)
        if contract is None:
            check = judge_rejection(result, comp, meta, rule, line, bounds, codes)
        else:
            check = judge_diagnostic(result, comp, rule, contract['diagnostic'], codes,
                                     primary_source=isolated, workspace=Path(tmp).resolve())
    check.trace = [trace_entry(command, result, 'compile', 'source')]
    check.input_hashes = {os.path.basename(path): source_hash}
    check.execution_context = execution_context(tmp)
    return check


def driver_warning_diagnostics(output, filename, primary_source, workspace=None):
    if not primary_source:
        raise SuiteError('single-source driver attribution needs the staged compilation input')
    primary = Path(primary_source)
    for text in output.splitlines():
        if INCLUDE_CONTEXT.match(text):
            return []
        header = reference_location_header(text)
        if header:
            location = reference_location(text, DECLARED_REF_LOC, header)
            if location is None:
                return []
            origin = Path(location.group(1))
            if workspace is not None:
                if not diagnostic_origin_matches(str(origin), filename, workspace):
                    return []
            elif ((origin.is_absolute() and origin != primary)
                    or (not origin.is_absolute() and str(origin) not in (filename, primary.name))):
                return []
    reported = []
    for text in output.splitlines():
        match = GNU_DRIVER_LINE.match(text)
        if match:
            line = int(match.group(2))
            reported.append(Diagnostic(line, line, set(), match.group(1), filename,
                                       'warning', 'single-source-driver'))
    return reported


def diagnostic_message_matches(message, predicate, normalize_exact=False):
    if 'equals_any' in predicate:
        normalized = message.strip().lower() if normalize_exact else message.lower()
        return any(normalized == (value.strip().lower() if normalize_exact else value.lower())
                   for value in predicate['equals_any'])
    messages = predicate.get('contains_any', [])
    return any(value.lower() in message.lower() for value in messages)


def nonfatal_matches(item, predicate, family):
    if predicate['compiler'] != family or predicate['severity'] != item.severity:
        return False
    if item.attribution != 'located' and predicate.get('attribution', 'located') != item.attribution:
        return False
    return diagnostic_message_matches(item.message, predicate)


def judge_diagnostic(result, comp, rule, diagnostic, codes=False, primary_source=None, *, workspace=None):
    failed = failure(result, 'compile')
    if failed:
        return failed
    filename = diagnostic['file']
    line = diagnostic['line']
    nonfatal = diagnostic.get('allow_nonfatal', [])
    if comp.family == 'lfortran':
        reported = lfortran_diagnostics(result.output)
    else:
        reported = list(reference_diagnostics(result.output, declared_input=True))
    if comp.family == 'gfortran' and any(
            predicate.get('attribution') == 'single-source-driver' for predicate in nonfatal):
        reported += driver_warning_diagnostics(result.output, filename, primary_source, workspace)
    matching = []
    for item in reported:
        if not diagnostic_origin_matches(item.file, filename, workspace):
            continue
        located = line <= item.first <= item.last <= diagnostic.get('end_line', line)
        if not located:
            continue
        if (('equals_any' in diagnostic or diagnostic.get('contains_any'))
                and not diagnostic_message_matches(item.message, diagnostic, normalize_exact=True)):
            continue
        if any(message.lower() in item.message.lower() for message in diagnostic.get('excludes_any', [])):
            continue
        allowed = item.severity in ('error', 'fatal error') or any(
            nonfatal_matches(item, predicate, comp.family) for predicate in nonfatal)
        if allowed:
            matching.append(item)
    if not matching:
        return Check('fail', 'expected located diagnostic was not reported', 'compile', result.output)
    if codes and comp.family == 'lfortran' and not any(rule in item.codes for item in matching):
        return Check('fail', f'detected without code {rule}', 'compile', result.output)
    note = 'diagnoses without rejection' if result.returncode == 0 else 'rejects'
    if all(item.attribution == 'single-source-driver' for item in matching):
        note += '; single-source driver attribution'
    return Check('pass', note, 'compile', result.output)


def judge_rejection(result, comp, meta, rule, line=None, bounds=None, codes=False,
                    diagnostic=None, phase='compile'):
    failed = failure(result, phase)
    if failed:
        return failed
    diagnostic = diagnostic or {}
    if 'equals_any' in diagnostic:
        raise SuiteError('diagnostic.equals_any requires compile-phase diagnose')
    filename = diagnostic.get('file')
    messages = diagnostic.get('contains_any', [])
    external = diagnostic.get('anchor') in ('eof', 'file') or phase == 'link'
    if external and messages and not any(message.lower() in result.output.lower() for message in messages):
        return Check('fail', 'expected diagnostic predicate was not reported', phase, result.output)
    if comp.family != 'lfortran' and result.returncode == 0:
        lo, hi = ((diagnostic['line'], diagnostic.get('end_line', diagnostic['line']))
                  if diagnostic.get('line') is not None else bounds or (1, float('inf')))
        warnings = reference_warning_lines(result.output, meta.reference_warnings, filename, messages)
        if any(lo <= location <= hi for location in warnings):
            return Check('pass', 'diagnoses without rejection', phase, result.output)
    if result.returncode == 0:
        return Check('fail', 'not rejected (compiler exited successfully)', phase, result.output)
    if external:
        if filename and Path(filename).name not in result.output:
            return Check('fail', 'diagnostic does not identify the expected file', phase, result.output)
        if not re.search(r'\berror\b', result.output, re.I):
            return Check('fail', 'rejected without an error diagnostic', phase, result.output)
        if codes and comp.family == 'lfortran' and not any(
                rule in error.codes for error in lfortran_errors(result.output)):
            return Check('fail', f'detected without code {rule}', phase, result.output)
        return Check('pass', 'rejects at external ' + diagnostic.get('anchor', 'link') + ' anchor',
                     phase, result.output)
    if comp.family != 'lfortran':
        lo, hi = ((diagnostic['line'], diagnostic.get('end_line', diagnostic['line']))
                  if diagnostic.get('line') is not None else bounds or (line, line))
        if any(lo <= location <= hi for location in reference_error_lines(result.output, filename, messages)):
            return Check('pass', 'rejects', phase, result.output)
        return Check('fail', 'rejected without a located case diagnostic', phase, result.output)
    errors = lfortran_errors(result.output)
    on_line = [error for error in errors
               if line <= error.first <= error.last <= diagnostic.get('end_line', line)
               and (filename is None or diagnostic_filename_matches(error.file, filename))
               and (not messages or any(message.lower() in error.message.lower()
                                        for message in messages))]
    if not on_line:
        return Check('fail', 'not detected on marked line', 'compile', result.output)
    tagged = any(rule in error.codes for error in on_line)
    if codes and not tagged:
        return Check('fail', f'detected without code {rule}', 'compile', result.output)
    extra = sorted((error.first, error.last) for error in errors if error not in on_line)
    note = '' if tagged else 'detected, no rule code'
    if extra:
        note += f'; other diagnostics at {extra}'
    return Check('pass', note, 'compile', result.output)


def launch_command(comp, meta, executable, arguments=None):
    return launch_argv(comp.configuration(), asdict(meta), executable, arguments or [])


def compiler_header_bytes(path):
    try:
        return Path(path).read_bytes()
    except OSError as error:
        raise SuiteError(f'{path}: cannot read the compiler binding header: {error}') from error


def compiler_binding_header(comp, timeout=30):
    if comp.c_binding_header:
        return comp.c_binding_header
    if comp.family == 'lfortran':
        option = '--print-c-include-dir'
    elif comp.family == 'gfortran':
        option = '-print-file-name=include'
    elif comp.family == 'flang':
        option = '-print-resource-dir'
    else:
        raise SuiteError(f'{comp.command}: no Fortran binding-header discovery for {comp.family}')
    result = run([comp.command, option], HERE, timeout)
    failed = failure(result, 'binding-header query')
    if failed or result.returncode:
        raise SuiteError(f'{comp.command}: binding-header query failed: '
                         + (failed.note if failed else excerpt(result.output)))
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise SuiteError(f'{comp.command}: binding-header query did not return one directory')
    directory = Path(lines[0])
    if not directory.is_absolute():
        raise SuiteError(f'{comp.command}: binding-header query returned a nonabsolute directory')
    name = 'ISO_Fortran_binding.h'
    if comp.family == 'flang':
        candidates = [directory / 'include' / name, directory / 'include/flang' / name]
        if len(directory.parents) >= 3:
            candidates.append(directory.parents[2] / 'include/flang' / name)
    else:
        candidates = [directory / name]
    existing = sorted({candidate.resolve() for candidate in candidates if candidate.is_file()})
    if not existing:
        raise SuiteError(f'{comp.command}: processor binding header not found from {option}')
    contents_by_path = {path: compiler_header_bytes(path) for path in existing}
    hashes = {hashlib.sha256(contents).hexdigest() for contents in contents_by_path.values()}
    if len(hashes) != 1:
        raise SuiteError(f'{comp.command}: ambiguous processor binding headers have different contents')
    path = existing[0]
    contents = contents_by_path[path]
    header = dict(path=str(path), sha256=hashlib.sha256(contents).hexdigest(),
                  discovery=option)
    version = re.search(rb'(?m)^\s*#\s*define\s+CFI_VERSION\s+([^\r\n]+)', contents)
    if version:
        header['cfi_version'] = version.group(1).decode('ascii', errors='backslashreplace').strip()
    validate_compiler_header(header, 'processor binding header')
    comp.c_binding_header = header
    return header


def check_fixture(fixture, comp, cc='cc', timeout=30, codes=False):
    meta = fixture.meta
    for profile in meta.profiles:
        checked = profile_check(comp, profile, timeout)
        if checked.outcome != 'pass':
            return checked
    trace = []
    hashes = {}
    headers = {}
    resources = {}
    with tempfile.TemporaryDirectory(prefix='conformance-fixture-') as tmp:
        workspace = Path(tmp).resolve()
        for filename in fixture.files:
            original = safe_path(fixture.root, filename)
            staged = safe_path(workspace, filename, exists=False)
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, staged)
            expected_hash = hashlib.sha256(original.read_bytes()).hexdigest()
            if hashlib.sha256(staged.read_bytes()).hexdigest() != expected_hash:
                raise SuiteError(f'{fixture.name}: staging changed bytes in {filename}')
            hashes[filename] = expected_hash

        def invoke(command, phase, step, stdin=None):
            result = run(command, tmp, timeout, stdin=stdin)
            trace.append(trace_entry(command, result, phase, step, stdin))
            return result

        def finish(check):
            check.trace = trace
            check.input_hashes = hashes
            check.compiler_headers = headers
            check.execution_context = execution_context(workspace, resources)
            return check

        expectation = fixture.expectation
        header_directory = None
        for step in fixture.build:
            source = str(safe_path(workspace, step.source))
            output = safe_path(workspace, step.output, exists=False)
            output.parent.mkdir(parents=True, exist_ok=True)
            selected_header_directory = None
            if step.language == 'c':
                if step.fortran_binding_header:
                    header = compiler_binding_header(comp, timeout)
                    contents = compiler_header_bytes(header['path'])
                    if hashlib.sha256(contents).hexdigest() != header['sha256']:
                        raise SuiteError(f'{comp.command}: processor binding header changed during the run')
                    if header_directory is None:
                        header_directory = Path(tempfile.mkdtemp(prefix='processor-header-', dir=tmp)).resolve()
                        staged_header = header_directory / 'ISO_Fortran_binding.h'
                        staged_header.write_bytes(contents)
                        if hashlib.sha256(staged_header.read_bytes()).hexdigest() != header['sha256']:
                            raise SuiteError('processor binding-header staging changed bytes')
                    headers['ISO_Fortran_binding.h'] = dict(header)
                    hashes['@compiler/ISO_Fortran_binding.h'] = header['sha256']
                    resources['ISO_Fortran_binding.h'] = str(header_directory / 'ISO_Fortran_binding.h')
                    selected_header_directory = str(header_directory)
            command = compile_command(comp.configuration(), asdict(meta), source, str(output),
                                      step.language, step.form, cc, selected_header_directory)
            result = invoke(command, 'compile', step.id)
            if expectation.phase == 'compile' and expectation.step == step.id:
                if expectation.outcome in ('reject', 'diagnose'):
                    diagnostic = expectation.diagnostic
                    judged_comp = comp if step.language == 'fortran' else Compiler(cc, 'c', '')
                    if expectation.outcome == 'diagnose':
                        return finish(judge_diagnostic(result, judged_comp, fixture.rule,
                                                       diagnostic, codes, primary_source=source,
                                                       workspace=workspace))
                    return finish(judge_rejection(
                        result, judged_comp, meta, fixture.rule, diagnostic.get('line'),
                        codes=codes, diagnostic=diagnostic))
                failed = failure(result, 'compile')
                if failed:
                    return finish(failed)
                if result.returncode:
                    return finish(Check('fail', f'compile step {step.id}: ' + excerpt(result.output),
                                        'compile', result.output))
                if not output.is_file():
                    return finish(Check('fail', 'compiler did not produce the declared object', 'compile'))
                return finish(Check('pass', phase='compile'))
            failed = failure(result, 'compile')
            if failed:
                return finish(failed)
            if result.returncode:
                return finish(Check('fail', f'compile step {step.id}: ' + excerpt(result.output),
                                    'compile', result.output))
            if not output.is_file():
                return finish(Check('fail', f'compile step {step.id} produced no object', 'compile'))
        link = fixture.link
        executable = safe_path(workspace, link['output'], exists=False)
        executable.parent.mkdir(parents=True, exist_ok=True)
        objects = [str(safe_path(workspace, name)) for name in link['objects']]
        command = link_command(comp.configuration(), asdict(meta), objects, str(executable),
                               link.get('driver', 'fortran'), cc)
        result = invoke(command, 'link', 'link')
        if expectation.phase == 'link' and expectation.outcome == 'reject':
            return finish(judge_rejection(result, comp, meta, fixture.rule, codes=codes,
                                          diagnostic=expectation.diagnostic, phase='link'))
        failed = failure(result, 'link')
        if failed:
            return finish(failed)
        if result.returncode:
            return finish(Check('fail', 'link failed: ' + excerpt(result.output), 'link', result.output))
        if not executable.is_file():
            return finish(Check('fail', 'linker did not produce the declared executable', 'link'))
        if expectation.phase == 'link':
            return finish(Check('pass', phase='link'))
        if meta.images > 1 and not comp.launcher:
            return finish(Check('skip', f'linked; needs a launcher for {meta.images} images', 'launch'))
        stdin = safe_path(workspace, fixture.stdin_file).read_bytes() if fixture.stdin_file else None
        result = invoke(launch_command(comp, meta, str(executable), fixture.arguments), 'run', 'run', stdin)
        failed = failure(result, 'run', compiler_process=False)
        if failed:
            return finish(failed)
        if result.returncode != expectation.exit_code:
            return finish(Check('fail', f'expected exit {expectation.exit_code}, got {result.returncode}',
                                'run', result.output))
        for stream in ('stdout', 'stderr'):
            allowed = getattr(expectation, stream)
            if allowed is not None:
                raw = getattr(result, stream + '_bytes')
                try:
                    observed = raw.decode('utf-8') if raw is not None else getattr(result, stream)
                except UnicodeDecodeError:
                    return finish(Check('fail', f'{stream} is not valid UTF-8 for its text oracle', 'run', result.output))
                if observed not in allowed:
                    return finish(Check('fail', f'{stream} differs from the declared oracle', 'run', result.output))
        for filename, allowed in expectation.files.items():
            output = safe_path(workspace, filename, exists=False)
            if not output.is_file():
                return finish(Check('fail', f'missing output file {filename}', 'run', result.output))
            try:
                observed = output.read_bytes().decode('utf-8')
            except UnicodeDecodeError:
                return finish(Check('fail', f'output file {filename} is not valid UTF-8', 'run', result.output))
            if observed not in allowed:
                return finish(Check('fail', f'output file {filename} differs from its oracle', 'run', result.output))
        for filename, expected_file in expectation.file_matches.items():
            output = safe_path(workspace, filename, exists=False)
            expected = safe_path(fixture.root, expected_file).read_bytes()
            if not output.is_file() or output.read_bytes() != expected:
                return finish(Check('fail', f'binary output file {filename} differs from its oracle', 'run', result.output))
        return finish(Check('pass', phase='run', output=result.output))


def _execute_case(case, comp, cc='cc', timeout=30, codes=False):
    if case.fixture:
        return check_fixture(case.fixture, comp, cc, timeout, codes)
    if case.kind == 'valid':
        return check_valid(case.path, comp, case.meta, timeout)
    for name in case.meta.profiles:
        checked = profile_check(comp, name, timeout)
        if checked.outcome != 'pass':
            return checked
    line, rule, _, bounds, source = case.isolated
    return check_invalid(case.path, source, line, rule, bounds, comp, case.meta, codes, timeout,
                         contract=case.contract)


def execute_case(case, comp, cc='cc', timeout=30, codes=False):
    check = _execute_case(case, comp, cc, timeout, codes)
    profiles = {}
    for name in case.meta.profiles:
        if name in comp.profiles:
            observation = asdict(comp.profiles[name])
            observation.pop('profile_checks')
            profiles[name] = observation
        else:
            profiles[name] = dict(outcome='not-run', note='Profile was not evaluated.')
    if any(check is value for value in comp.profiles.values()):
        return replace(check, trace=[], input_hashes={}, execution_context={}, profile_checks=profiles)
    return replace(check, profile_checks=profiles)


def status(name, check, xfail, review=None):
    if check.outcome == 'error':
        return 'ERROR'
    if review is not None and not review.approved:
        return review.state.upper().replace('-', '_')
    if check.outcome in ('skip', 'error'):
        return check.outcome.upper()
    if name in xfail:
        return 'XPASS' if check.outcome == 'pass' else 'XFAIL'
    return check.outcome.upper()


def read_xfail(path):
    if not os.path.exists(path):
        return []
    return [line for line in Path(path).read_text().splitlines() if line.split('#')[0].strip()]


def update_xfail(path, results):
    unapproved = [r['name'] for r in results if not r.get('review', Review()).approved]
    if unapproved:
        raise SuiteError('cannot update xfails for unapproved fixtures: ' + ', '.join(unapproved))
    ran = {r['name'] for r in results if r['check'].outcome in ('pass', 'fail')}
    kept = [line for line in read_xfail(path) if line.split('#')[0].strip() not in ran]
    new = [f"{r['name']}  # {r['check'].note}".rstrip()
           for r in results if r['check'].outcome == 'fail']
    Path(path).write_text('\n'.join(sorted(kept + new)) + '\n')


def safely(check, *args):
    try:
        return check(*args)
    except SuiteError as error:
        return Check('error', str(error), 'harness')


def reference_label(check, kind):
    if check.outcome == 'pass':
        if check.note.startswith('diagnoses without rejection'):
            return 'diagnoses'
        if kind == 'invalid':
            return 'rejects'
        return {'compile': 'compiles', 'link': 'links', 'run': 'runs'}.get(check.phase, 'passes')
    if check.outcome == 'skip':
        return 'skip'
    if check.outcome == 'error':
        return 'error'
    if check.phase == 'run':
        return 'runtime-fail'
    if 'crashed' in check.note or 'timed out' in check.note:
        return 'crash/timeout'
    return 'rejects' if kind == 'valid' else 'unconfirmed'


def record_fixture_review(registry, cases, key, state, rationale, sources, report_path=None):
    selected = [case for case in cases if case.review_key == key]
    if not selected:
        raise SuiteError('unknown fixture review key: ' + key)
    _, fingerprints = case_review_bindings(selected, registry)
    fingerprint = fingerprints[key]
    if not sources:
        rule = selected[0].rule
        if rule in registry.requirements:
            requirement = registry.requirements[rule]
            sources = [registry.requirement_sections[rule] + '#' + unit
                       for unit in requirement['source_units']]
        elif rule in registry.legacy:
            sources = registry.legacy[rule].get('source_units', [registry.legacy[rule]['source']])
        else:
            sources = [rule]
    evidence = []
    if state == 'reference-validated' and not report_path:
        raise SuiteError('reference validation requires --review-report')
    if report_path:
        report = json.loads(Path(report_path).read_text())
        if report.get('run_errors'):
            raise SuiteError('reference report is provisional because its inputs or toolchain changed')
        observations = {result['name']: result for result in report['results']}
        versions = {item['command']: item for item in report['compilers']}
        for case in selected:
            observation = observations.get(case.name)
            if not observation or observation.get('review', {}).get('fingerprint') != fingerprint:
                raise SuiteError(f'{case.name}: report does not describe the current fixture fingerprint')
            references = list(observation['references'].items())
            if set(observation['references']) - set(versions):
                raise SuiteError(f'{case.name}: reference observation has no compiler identity')
            if state == 'reference-validated' and not any(
                    qualifying_reference(case, dict(check, standard=versions[name]['standard']))
                    for name, check in references):
                raise SuiteError(f'{case.name}: no successful reference at the required phase and supported mode')
            for name, check in references:
                item = dict(case=case.name, compiler=os.path.basename(name),
                            version=versions[name]['version'], standard=versions[name]['standard'],
                            phase=check['phase'], outcome=check['outcome'])
                headers = check.get('compiler_headers', {})
                needs_header = case.fixture and any(step.fortran_binding_header for step in case.fixture.build)
                if needs_header and check['outcome'] == 'pass' and set(headers) != {'ISO_Fortran_binding.h'}:
                    raise SuiteError(f'{case.name}: successful descriptor observation lacks header provenance')
                if headers:
                    if not needs_header:
                        raise SuiteError(f'{case.name}: report claims an undeclared compiler header')
                    if set(headers) != {'ISO_Fortran_binding.h'}:
                        raise SuiteError(f'{case.name}: unknown compiler-header evidence')
                    validate_compiler_header(headers['ISO_Fortran_binding.h'], f'{case.name} header')
                    if headers['ISO_Fortran_binding.h'] != versions[name].get('c_binding_header'):
                        raise SuiteError(f'{case.name}: descriptor header differs from the compiler snapshot')
                    if not report.get('c_compiler'):
                        raise SuiteError(f'{case.name}: descriptor observation lacks a C companion identity')
                    item.update(compiler_headers=headers, c_compiler=report['c_compiler'])
                evidence.append(item)
    registry.record_review(key, fingerprint, state, rationale, sources, evidence)


def combined_references(references):
    values = list(references.values())
    if any(value.outcome == 'error' for value in values):
        return Check('error', 'reference infrastructure failed', 'reference')
    if any(value.outcome == 'fail' for value in values):
        return Check('fail', 'one or more reference expectations failed', 'reference')
    if all(value.outcome == 'skip' for value in values):
        return Check('skip', 'all references skipped', 'reference')
    return Check('pass', phase='reference')


def tool_version(command, timeout):
    result = run([command, '--version'], HERE, timeout)
    if result.returncode or failure(result, 'version query'):
        raise SuiteError(f'{command}: version query failed')
    banner = next((line for line in result.output.splitlines() if line.strip()), '')
    if not banner:
        raise SuiteError(f'{command}: empty version response')
    return banner


def confirm_snapshot(compilers, cases, fingerprints, timeout=30, companion=None, evidence_snapshot=None,
                     execution_snapshot=None, source_use_snapshot=None):
    errors = []
    try:
        current_registry = Registry()
        current_cases = (collect_cases(HERE, current_registry)
                         if cases or evidence_snapshot is not None or execution_snapshot is not None else [])
        by_name = {case.name: case for case in current_cases}
        for case in cases:
            current = by_name.get(case.name)
            if current is None:
                errors.append(f'{case.name}: selected execution disappeared during the run')
            elif (current.review_key != case.review_key
                  or current.fingerprint(current_registry) != fingerprints[case.review_key]):
                errors.append(f'{case.review_key}: inputs or requirement changed during the run')
        if evidence_snapshot is not None or execution_snapshot is not None:
            if (evidence_snapshot is not None
                    and current_registry.evidence.snapshot(current_cases) != evidence_snapshot):
                errors.append('canonical evidence links, dependencies, or reviews changed during the run')
            if (execution_snapshot is not None
                    and current_registry.execution.snapshot(current_cases) != execution_snapshot):
                errors.append('execution aggregate, complete case universe, source census, or reviews changed during the run')
        if source_use_snapshot is not None and current_registry.source_uses.snapshot() != source_use_snapshot:
            errors.append('source-use inventory, source scope, dependencies, or reviews changed during the run')
    except (SuiteError, OSError) as error:
        errors.append('cannot confirm fixture snapshot: ' + str(error))
    for comp in compilers:
        try:
            current = compiler(comp.command, comp.family == 'lfortran', comp.standard, comp.launcher, timeout)
            if (current.family, current.version) != (comp.family, comp.version):
                errors.append(f'{comp.command}: compiler version changed during the run')
        except SuiteError as error:
            errors.append('cannot confirm compiler snapshot: ' + str(error))
        if comp.c_binding_header:
            try:
                actual = hashlib.sha256(compiler_header_bytes(comp.c_binding_header['path'])).hexdigest()
                if actual != comp.c_binding_header['sha256']:
                    errors.append(f'{comp.command}: processor binding header changed during the run')
            except SuiteError as error:
                errors.append('cannot confirm binding-header snapshot: ' + str(error))
    if companion:
        try:
            if tool_version(companion['command'], timeout) != companion['version']:
                errors.append('C companion compiler version changed during the run')
        except SuiteError as error:
            errors.append('cannot confirm C compiler snapshot: ' + str(error))
    return sorted(set(errors))


def relevant_links(links, cases):
    identifiers = {case.name for case in cases}
    rules = {case.rule for case in cases}
    return [link for link in links if link['target']['requirement'] in rules
            or any(member['id'] in identifiers for member in link['cases'])]


def print_links(links):
    for link in links:
        target = link['target']
        print(f"LINK {link['state'].upper()} {link['id']} -> {target['requirement']}/{target['facet']}"
              ' [finite linked evidence; no derived pass/effect count]')
        for member in link['cases']:
            print(f"  {member['role']}: {member['id']} [{member['primary_rule']};"
                  f" {member['phase']}; fixture review={member['review']['state']}]")
        if link['blockers']:
            print('  blockers: ' + '; '.join(link['blockers']))


def print_execution_aggregates(aggregates):
    for aggregate in aggregates:
        print(f"AGGREGATE {aggregate['state'].upper()} {aggregate['id']}"
              f" [{aggregate['member_count']} collected cases; observational only;"
              ' no new execution, facet completion, or universal conformance credit]')
        if aggregate['blockers']:
            print('  blockers: ' + '; '.join(aggregate['blockers']))


def print_source_uses(inventories):
    for inventory in inventories:
        counts = inventory['disposition_counts']
        print(f"SOURCE-USE {inventory['state'].upper()} {inventory['id']}"
              f" [{inventory['source_unit_count']} source units;"
              f" {counts['pending']} pending; {counts['missing']} missing;"
              ' no new execution or facet-completion credit]')
        if inventory['blockers']:
            print('  blockers: ' + '; '.join(inventory['blockers']))


def evidence_observations(links, results, compilers, reference_only):
    linked = copy.deepcopy(links)
    by_id = {result['name']: result for result in results}
    identities = {comp.command: dict(command=comp.command, family=comp.family,
                                     version=comp.version, standard=comp.standard) for comp in compilers}
    target = next((comp.command for comp in compilers if comp.family == 'lfortran'), None)

    def observation(command, check):
        return dict(identities[command], outcome=check.outcome, phase=check.phase, note=check.note)

    for link in linked:
        for member in link['cases']:
            result = by_id.get(member['id'])
            member['observation_state'] = 'present' if result else 'not-selected'
            member['target_observation'] = (
                observation(target, result['check']) if result and not reference_only else None)
            member['reference_observations'] = (
                [observation(command, check) for command, check in result['references'].items()]
                if result else [])
    return linked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--test', action='append', help='repeatable substring filter on file name or rule ID')
    ap.add_argument('--lfortran', default='lfortran')
    ap.add_argument('--std', default='f23')
    ap.add_argument('--reference', action='append', default=[],
                    help='reference compiler (repeatable), e.g. gfortran, flang')
    ap.add_argument('--reference-std', default='auto',
                    help='auto probes f2023 then f2018; an explicit mode overrides this')
    ap.add_argument('--reference-only', action='store_true', help='run reference checks without LFortran or its xfail baseline')
    ap.add_argument('--cc', default='cc', help='C compiler for declared C build steps')
    ap.add_argument('--launcher', action='append', default=[],
                    help='COMPILER=COMMAND with {images} and optional {exe}; no shell is used')
    ap.add_argument('--timeout', type=float, default=30, help='seconds per compiler or executable invocation')
    ap.add_argument('--codes', action='store_true', help='require the rule code in the diagnostic')
    ap.add_argument('--update-xfail', action='store_true')
    ap.add_argument('--coverage', help='path to doc/fortran_2023_rules.txt: print per-rule coverage')
    ap.add_argument('--report', help='write JSON results, compiler versions, and complete diagnostics')
    ap.add_argument('--list', action='store_true', help='validate and list selected files without compiling')
    ap.add_argument('--audit', action='store_true', help='audit all catalogues, source accounting, and fixture approvals')
    ap.add_argument('--require-complete-source', action='store_true', help='fail an audit while source census/review is incomplete')
    ap.add_argument('--allow-unreviewed', action='store_true', help='collect draft observations; never permitted with --update-xfail')
    ap.add_argument('--no-skips', action='store_true', help='require actual results from every selected compiler')
    ap.add_argument('--record-review', metavar='FIXTURE', help='explicitly adjudicate a fixture without running compilers')
    ap.add_argument('--record-catalogue-review', metavar='SECTION',
                    help='record a content-bound source/catalogue review without running compilers')
    ap.add_argument('--record-evidence-review', metavar='LINK',
                    help='independently adjudicate a canonical case link after source and fixture reviews')
    ap.add_argument('--record-execution-review', metavar='AGGREGATE',
                    help='independently review a finite execution aggregate and its complete case inventory')
    ap.add_argument('--record-source-use-review', metavar='INVENTORY',
                    help='independently review a finite source-use inventory without compiler evidence')
    ap.add_argument('--review-state', choices=['source-reviewed', 'reference-validated', 'unreviewed', 'disputed', 'needs-oracle'])
    ap.add_argument('--review-rationale')
    ap.add_argument('--review-source', action='append', default=[])
    ap.add_argument('--review-report', help='fingerprinted observations required for reference-validated approval')
    a = ap.parse_args()
    if not 0 < a.timeout < float('inf'):
        ap.error('--timeout must be positive and finite')
    if a.reference_only and not a.reference:
        ap.error('--reference-only needs at least one --reference')
    if a.reference_only and a.codes:
        ap.error('--codes applies to the LFortran target, not a reference-only run')
    if a.require_complete_source and not a.audit:
        ap.error('--require-complete-source must be used with --audit')
    if sum(bool(value) for value in (
            a.record_review, a.record_catalogue_review, a.record_evidence_review,
            a.record_execution_review, a.record_source_use_review, a.audit, a.list)) > 1:
        ap.error('--record-review, --record-catalogue-review, --record-evidence-review, --audit,'
                 ' --record-execution-review, --record-source-use-review, and --list are separate operations')
    if a.update_xfail and (a.record_review or a.record_catalogue_review or a.record_evidence_review
                          or a.record_execution_review or a.record_source_use_review or a.audit or a.list):
        ap.error('--update-xfail is a separate execution operation')
    if a.update_xfail and (a.allow_unreviewed or a.reference_only):
        ap.error('--update-xfail is only for approved LFortran fixtures')
    if a.record_review and (not a.review_state or not a.review_rationale):
        ap.error('--record-review needs --review-state and --review-rationale')
    if a.record_catalogue_review and not a.review_rationale:
        ap.error('--record-catalogue-review needs --review-rationale')
    if a.record_catalogue_review and (a.review_state or a.review_source or a.review_report):
        ap.error('fixture review options do not apply to a catalogue review')
    if a.record_evidence_review:
        if not a.review_state or not a.review_rationale:
            ap.error('--record-evidence-review needs --review-state and --review-rationale')
        if a.review_state == 'reference-validated' or a.review_source or a.review_report:
            ap.error('link adjudication uses its declared source/basis anchors, not a compiler report')
    if a.record_execution_review:
        if not a.review_state or not a.review_rationale:
            ap.error('--record-execution-review needs --review-state and --review-rationale')
        if a.review_state == 'reference-validated' or a.review_source or a.review_report:
            ap.error('aggregate adjudication uses source and the complete inventory, not a compiler report')
    if a.record_source_use_review:
        if not a.review_state or not a.review_rationale:
            ap.error('--record-source-use-review needs --review-state and --review-rationale')
        if a.review_state == 'reference-validated' or a.review_source or a.review_report:
            ap.error('source-use adjudication uses its complete source universe, not a compiler report')
    if not (a.record_review or a.record_catalogue_review or a.record_evidence_review
            or a.record_execution_review or a.record_source_use_review) and (
            a.review_state or a.review_rationale or a.review_source or a.review_report):
        ap.error('review options require a review operation')
    xfail_path = os.path.join(HERE, 'expected_failures.txt')
    xfail = set() if a.reference_only else {line.split('#')[0].strip() for line in read_xfail(xfail_path)}
    try:
        registry = Registry()
        if a.record_source_use_review:
            registry.source_uses.record_review(a.record_source_use_review, a.review_state, a.review_rationale)
            print('Recorded independent finite source-use review:', a.record_source_use_review, a.review_state)
            return 0
        all_cases = collect_cases(HERE, registry)
        selected = select_cases(all_cases, a.test)
        if not selected:
            raise SuiteError('no cases selected')
        reviews = {}
        review_groups, fingerprints = case_review_bindings(all_cases, registry)
        for key, fingerprint in fingerprints.items():
            reviews[key] = registry.review(key, fingerprint, review_groups[key])
        if a.record_catalogue_review:
            registry.record_catalogue_review(a.record_catalogue_review, a.review_rationale)
            print('Recorded content-bound catalogue review:', a.record_catalogue_review)
            return 0
        if a.record_review:
            record_fixture_review(registry, all_cases, a.record_review, a.review_state,
                                  a.review_rationale, a.review_source, a.review_report)
            print('Recorded explicit fixture review:', a.record_review, a.review_state)
            return 0
        if a.record_evidence_review:
            registry.evidence.record_review(all_cases, a.record_evidence_review, a.review_state, a.review_rationale)
            print('Recorded independent canonical-link review:', a.record_evidence_review, a.review_state)
            return 0
        if a.record_execution_review:
            registry.execution.record_review(all_cases, a.record_execution_review,
                                             a.review_state, a.review_rationale)
            print('Recorded independent finite execution-aggregate review:',
                  a.record_execution_review, a.review_state)
            return 0
        links = registry.evidence.report(all_cases)
        aggregates = registry.execution.report(all_cases)
        source_uses = registry.source_uses.report()
        selected_links = relevant_links(links, selected)
        unapproved_links = any(link['state'] != 'current' for link in selected_links)
        unapproved_execution = any(item['state'] != 'current' for item in aggregates)
        evidence_snapshot = {link['id']: dict(fingerprint=link['review']['fingerprint'], state=link['state'])
                             for link in links}
        execution_snapshot = {item['id']: dict(fingerprint=item['review']['fingerprint'], state=item['state'])
                              for item in aggregates}
        source_use_snapshot = registry.source_uses.snapshot()
        if a.audit:
            registry.render()
            audit = registry.audit(all_cases)
            summary = {key: value for key, value in audit.items() if key != 'sections_without_catalogues'}
            summary['fixture_review_states'] = dict(collections.Counter(review.state for review in reviews.values()))
            print(json.dumps(summary, indent=2))
            if a.report:
                Path(a.report).write_text(json.dumps(dict(audit, fixture_reviews={
                    key: asdict(value) for key, value in reviews.items()}), indent=2) + '\n')
            unapproved = any(not review.approved for review in reviews.values())
            return int((a.require_complete_source and not audit['complete_source'])
                       or ((unapproved or any(link['state'] != 'current' for link in links)
                            or unapproved_execution or any(item['state'] != 'current' for item in source_uses))
                           and not a.allow_unreviewed))
        if a.list:
            for case in selected:
                print(f'{case.rule:20} {case.kind:7} {case.name}'
                      f' [{case.meta.evidence}; review={reviews[case.review_key].state}]')
            print_links(selected_links)
            print_execution_aggregates(aggregates)
            print_source_uses(source_uses)
            return 0
        if a.update_xfail:
            pending = [case.review_key for case in selected if not reviews[case.review_key].approved]
            if pending:
                raise SuiteError('cannot update xfails for unapproved fixtures: ' + ', '.join(sorted(set(pending))))
            if unapproved_links:
                raise SuiteError('cannot update xfails with unreviewed/stale linked evidence: ' + ', '.join(
                    link['id'] for link in selected_links if link['state'] != 'current'))
            if unapproved_execution:
                raise SuiteError('cannot update xfails with unreviewed/stale execution aggregates: ' + ', '.join(
                    item['id'] for item in aggregates if item['state'] != 'current'))
        launchers = {}
        for value in a.launcher:
            name, separator, command = value.partition('=')
            if not separator or not name or not command.strip() or name in launchers:
                raise SuiteError('--launcher requires a unique COMPILER=COMMAND')
            launchers[name] = shlex.split(command)
        unknown = set(launchers) - {a.lfortran, *a.reference}
        if unknown:
            raise SuiteError('launcher has no selected compiler: ' + ', '.join(sorted(unknown)))
        lf = None if a.reference_only else compiler(a.lfortran, True, a.std, launchers.get(a.lfortran, []), a.timeout)
        refs = [compiler(name, False, a.reference_std, launchers.get(name, []), a.timeout)
                for name in dict.fromkeys(a.reference)]
        companion = (dict(command=a.cc, version=tool_version(a.cc, a.timeout))
                     if any(case.fixture and uses_c_companion(case.fixture)
                            for case in selected) else None)
    except SuiteError as error:
        print('ERROR:', error, file=sys.stderr)
        return 2

    compilers = ([lf] if lf else []) + refs
    for comp in compilers:
        print(f'compiler {comp.command}: {comp.version}; standard={comp.standard}')
    results = []
    for case in selected:
        check = safely(execute_case, case, lf, a.cc, a.timeout, a.codes) if lf else None
        references = {r.command: safely(execute_case, case, r, a.cc, a.timeout, False) for r in refs}
        results.append(dict(name=case.name, rule=case.rule, kind=case.kind,
                            check=check if check is not None else combined_references(references),
                            metadata=case.meta, references=references,
                            review=reviews[case.review_key], review_key=case.review_key))
    run_errors = (confirm_snapshot(compilers, selected, fingerprints, a.timeout, companion,
                                   evidence_snapshot, execution_snapshot, source_use_snapshot)
                  if a.report or a.update_xfail else [])
    compiler_records = [
        dict(command=c.command, family=c.family, standard=c.standard,
             version=c.version, launcher=c.launcher, wrapper=c.wrapper,
             c_binding_header=c.c_binding_header) for c in compilers]
    result_records = [
        dict(name=r['name'], rule=r['rule'], kind=r['kind'],
             status=status(r['name'], r['check'], xfail, r['review']),
             check=asdict(r['check']), metadata=asdict(r['metadata']),
             review=asdict(r['review']), review_key=r['review_key'],
             references={name: asdict(check) for name, check in r['references'].items()})
        for r in results]
    try:
        execution_reports = execution_observations(
            aggregates, result_records, compiler_records, a.reference_only, run_errors, companion,
            source_root=registry.root) if aggregates else []
    except SuiteError as error:
        run_errors.append('cannot aggregate execution evidence: ' + str(error))
        execution_reports = [dict(item, observations=[], provisional=True, run_errors=list(run_errors))
                             for item in aggregates]
    for error in run_errors:
        print('ERROR: provisional results:', error, file=sys.stderr)

    width = max(len(r['name']) for r in results)
    for result in results:
        check = result['check']
        reference = '  '.join(f'{os.path.basename(name)}={reference_label(value, result["kind"])}'
                              for name, value in result['references'].items())
        evidence = result['metadata'].evidence
        annotation = '' if evidence == 'effect' else f' [{evidence}; not full effect coverage]'
        if result['metadata'].oracle_basis != 'standard':
            annotation += f" [oracle={result['metadata'].oracle_basis}"
            if result['metadata'].oracle_profile:
                annotation += ':' + result['metadata'].oracle_profile
            annotation += ']'
        print(f'{status(result["name"], check, xfail, result["review"]):12} {result["name"]:{width}}'
              f'  {reference:34} {check.note}{annotation}')
        if not result['review'].approved:
            print(f'      observed={check.outcome}; review: {result["review"].rationale}')
        for comp in refs:
            ref = result['references'][comp.command]
            if ref.outcome != 'pass':
                mode = f' ({comp.standard}; case needs {result["metadata"].standard})' if (
                    result['metadata'].standard and result['metadata'].standard != comp.standard) else ''
                print(f'      {comp.command}{mode}: {ref.note}')
    counts = collections.Counter(status(r['name'], r['check'], xfail, r['review']) for r in results)
    print('\n' + ', '.join(f'{k}: {v}' for k, v in sorted(counts.items())))
    if refs:
        agree = sum(all(v.outcome == 'pass' for v in r['references'].values()) for r in results)
        print(f'reference compilers all agree with the test on {agree}/{len(results)} cases')
    print_links(selected_links)
    print_execution_aggregates(aggregates)
    print_source_uses(source_uses)
    if a.update_xfail:
        if run_errors:
            print('Expected failures were not modified because the run was not a consistent snapshot.')
        else:
            update_xfail(xfail_path, results)
            print('updated', xfail_path)
    if a.coverage:
        rules = list(dict.fromkeys(re.findall(r'^([RC]\d+)\b', Path(a.coverage).read_text(), re.M)))
        per = collections.defaultdict(collections.Counter)
        for result in results:
            c = per[result['rule']]
            kind = result['kind']
            c[kind] += 1
            c[kind + '_pass'] += result['check'].outcome == 'pass'
            c['skipped'] += result['check'].outcome == 'skip'
        both = [rule for rule in rules if per[rule]['valid'] and per[rule]['invalid']]
        print(f'\nR/C inventory: {len(both)}/{len(rules)} rules have both valid and invalid cases')
        for rule in rules + sorted(rule for rule in per if rule.startswith('S')):
            c = per[rule]
            if c['valid'] or c['invalid']:
                print(f"  {rule:20} valid {c['valid_pass']}/{c['valid']}"
                      f"   invalid detected {c['invalid_pass']}/{c['invalid']}   skipped {c['skipped']}")
        print('Case counts are not facet completeness; positive controls and context-only cases'
              ' do not establish the corresponding restriction or undefined-result effect.')
        source_audit = registry.audit(all_cases)
        print(f"Source accounting: {source_audit['accounted_base_units']}/{source_audit['base_source_units']}"
              f" base units accounted for; {source_audit['unresolved_base_units']} unresolved."
              f" Census review: {source_audit['source_inventory_review']}.")
    if a.report:
        report = {
            'compilers': compiler_records,
            'source_root': str(registry.root),
            'reference_only': a.reference_only,
            'run_errors': run_errors,
            'c_compiler': companion,
            'source_audit': registry.audit(all_cases),
            'evidence_links': evidence_observations(links, results, compilers, a.reference_only),
            'execution_aggregates': execution_reports,
            'source_use_inventories': source_uses,
            'results': result_records,
        }
        Path(a.report).write_text(json.dumps(report, indent=2) + '\n')
    failed = any(status(r['name'], r['check'], xfail) in ('FAIL', 'XPASS', 'ERROR') for r in results)
    unapproved = any(not result['review'].approved for result in results)
    skipped = any(result['check'].outcome == 'skip' or any(
        check.outcome == 'skip' for check in result['references'].values()) for result in results)
    return 2 if run_errors else int(
        failed or ((unapproved or unapproved_links or unapproved_execution) and not a.allow_unreviewed)
        or (a.no_skips and skipped))


if __name__ == '__main__':
    sys.exit(main())
