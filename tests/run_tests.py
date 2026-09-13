#!/usr/bin/env python3
"""Run self-checking programs and isolated diagnostic cases.

See tests/README.md for metadata, profiles, case boundaries, and coverage.
Reference results corroborate fixtures; they never determine LFortran's verdict.
"""
import argparse
import collections
from dataclasses import asdict, dataclass, field
import glob
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import tempfile
from typing import Dict, List, Set

HERE = os.path.dirname(os.path.abspath(__file__))
RULE = r'(?:[RC]\d+|S\d+(?:\.\d+)+(?:-\d{3})?)'
MARK = re.compile(r'!\s*\{error\s+(' + RULE + r')(?:\s+([\w-]+))?\}')
NAME = re.compile(r'^([RC]\d+|S[\d_]+)_(valid|invalid)(?:__([a-z][\w-]*))?\.f(90)?$')
SHORT = re.compile(
    r'^(.*?):(\d+)-(\d+):(\d+)-(\d+): (.*?) error'
    r'(?: \[([\w.-]+)\])?(?: \(F2023 ([^)]+)\))?: (.*)$', re.I)
REF_LOC = re.compile(r'^.*?\.f(?:90)?:(\d+):(\d+)(?::|\s|$)')
HEADER = re.compile(r'^!\s*(rule|covers|evidence|requires|profile|images|standard|reference-warnings):\s*(.*?)\s*$')
CASE = re.compile(r'^!\s*case:\s*([\w-]+)\s*$')
ICE = re.compile(r'internal compiler error|LCOMPILERS_ASSERT|assertion .*failed|'
                 r'LLVM ERROR|segmentation fault|PLEASE submit a bug report', re.I)
PROFILES = {'two-integer-kinds', 'two-logical-kinds', 'integer-range-nine', 'iso10646', 'ieee-binary'}


class SuiteError(Exception):
    pass


@dataclass
class ProcessResult:
    returncode: int
    output: str
    timed_out: bool = False


@dataclass
class Diagnostic:
    first: int
    last: int
    codes: Set[str]
    message: str


@dataclass
class Check:
    outcome: str
    note: str = ''
    phase: str = ''
    output: str = ''


@dataclass
class Metadata:
    facets: List[str] = field(default_factory=list)
    evidence: str = 'effect'
    coarray: bool = False
    profiles: List[str] = field(default_factory=list)
    images: int = 1
    standard: str = ''
    reference_warnings: List[str] = field(default_factory=list)


@dataclass
class Compiler:
    command: str
    family: str
    standard: str
    version: str = ''
    launcher: List[str] = field(default_factory=list)
    profiles: Dict[str, Check] = field(default_factory=dict)

    def flags(self, path, meta):
        if self.family == 'lfortran':
            flags = ['--std=' + self.standard, '--no-color']
            if path.endswith('.f'):
                flags.append('--fixed-form')
            if meta.coarray:
                flags.append('--coarray')
        else:
            flags = ['-std=' + self.standard]
            if self.family == 'gfortran':
                flags.append('-fdiagnostics-color=never')
            if path.endswith('.f'):
                flags.append('-ffixed-form')
            if meta.coarray:
                if self.family == 'flang':
                    flags.append('-fcoarray')
                elif os.path.basename(self.command) != 'caf':
                    flags.append('-fcoarray=lib' if self.launcher else '-fcoarray=single')
        return flags


def canonical_rule(name):
    if not name.startswith('S'):
        return name
    parts = name[1:].split('_')
    if len(parts[-1]) == 3:
        return 'S' + '.'.join(parts[:-1]) + '-' + parts[-1]
    return 'S' + '.'.join(parts)


def discover(root, patterns=None):
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
    if not tests:
        raise SuiteError('no tests discovered in ' + root)
    return tests


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
    return Metadata(values.get('covers', '').split(), evidence,
                    'coarray' in requires, profiles, images, standard, warnings)


def run(cmd, cwd, timeout=30):
    try:
        process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True,
                                   start_new_session=True)
    except OSError as error:
        raise SuiteError(f'cannot start {cmd[0]}: {error}') from error
    timed_out = False
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        output, _ = process.communicate()
    return ProcessResult(process.returncode, output, timed_out)


def failure(result, phase):
    if result.timed_out:
        return Check('fail', f'{phase} timed out', phase, result.output)
    if 'ASR verify pass error' in result.output:
        return Check('fail', f'{phase} failed ASR verification', phase, result.output)
    if result.returncode < 0 or result.returncode >= 128 or ICE.search(result.output):
        return Check('fail', f'{phase} crashed (exit {result.returncode})',
                     phase, result.output)
    return None


def excerpt(output):
    lines = output.strip().splitlines()
    errors = [line for line in lines if re.search(r'error|not yet implemented', line, re.I)]
    return (errors or lines or ['no diagnostic output'])[0][:180]


def compiler(command, is_lfortran, standard, launcher, timeout):
    version = run([command, '--version'], HERE, timeout)
    if version.returncode != 0 or failure(version, 'version query'):
        raise SuiteError(f'{command}: version query failed: {excerpt(version.output)}')
    if is_lfortran:
        family = 'lfortran'
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
    return Compiler(command, family, standard,
                    version.output.splitlines()[0], launcher)


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


def lfortran_errors(output):
    found = []
    for line in output.splitlines():
        m = SHORT.match(line)
        if m and 'warning' not in m.group(6).lower():
            codes = set(re.findall(RULE, m.group(8) or ''))
            if m.group(7):
                codes.add(m.group(7))
            found.append(Diagnostic(int(m.group(2)), int(m.group(3)), codes, m.group(9)))
    return found


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


def reference_messages(output):
    pending = None
    for line in output.splitlines():
        location = REF_LOC.match(line)
        message = line
        if location:
            pending = int(location.group(1))
            message = line[location.end():].lstrip()
        diagnostic = re.match(r'^(Error|Fatal Error|Warning|portability):\s*(.*)', message, re.I)
        if diagnostic:
            if pending is not None:
                yield pending, diagnostic.group(1).lower(), diagnostic.group(2)
            pending = None


def reference_error_lines(output):
    return {line for line, severity, _ in reference_messages(output)
            if severity in ('error', 'fatal error')}


def reference_warning_lines(output, allowed):
    return {line for line, severity, message in reference_messages(output)
            if severity in ('warning', 'portability')
            and set(re.findall(r'\[-W([\w-]+)\]', message)).intersection(allowed)}


def profile_check(comp, name, timeout):
    if name in comp.profiles:
        return comp.profiles[name]
    source = os.path.join(HERE, 'profiles', name.replace('-', '_') + '.f90')
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, 'a.out')
        result = run([comp.command] + comp.flags(source, Metadata()) + [source, '-o', exe], tmp, timeout)
        check = failure(result, 'profile compilation')
        if check is None and result.returncode != 0:
            check = Check('fail', 'profile does not compile: ' + excerpt(result.output),
                          'profile', result.output)
        if check is None:
            result = run([exe], tmp, timeout)
            check = failure(result, 'profile execution')
            if check is None:
                if result.returncode == 77:
                    check = Check('skip', 'profile unavailable: ' + name, 'profile', result.output)
                elif result.returncode != 0:
                    check = Check('fail', 'profile failed: ' + name, 'profile', result.output)
                else:
                    check = Check('pass')
    comp.profiles[name] = check
    return check


def check_valid(path, comp, meta, timeout=30):
    for name in meta.profiles:
        check = profile_check(comp, name, timeout)
        if check.outcome != 'pass':
            return check
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, 'a.out')
        result = run([comp.command] + comp.flags(path, meta) + [path, '-o', exe], tmp, timeout)
        failed = failure(result, 'compilation')
        if failed:
            return failed
        if result.returncode != 0:
            return Check('fail', 'does not compile: ' + excerpt(result.output), 'compile', result.output)
        if meta.images > 1 and not comp.launcher:
            return Check('skip', f'compiled; needs a launcher for {meta.images} images', 'launch')
        command = [exe]
        if meta.coarray and comp.launcher:
            command = [token.replace('{images}', str(meta.images)).replace('{exe}', exe)
                       for token in comp.launcher]
            if not any('{exe}' in token for token in comp.launcher):
                command.append(exe)
        result = run(command, tmp, timeout)
        failed = failure(result, 'execution')
        if failed:
            return failed
        if result.returncode != 0:
            return Check('fail', f'runtime exit code {result.returncode}: ' + excerpt(result.output),
                         'run', result.output)
    return Check('pass', phase='run')


def check_invalid(path, source, line, rule, bounds, comp, meta, codes=False, timeout=30):
    with tempfile.TemporaryDirectory() as tmp:
        isolated = os.path.join(tmp, os.path.basename(path))
        Path(isolated).write_text(source)
        flags = comp.flags(path, meta)
        if comp.family == 'lfortran':
            flags += ['--semantics-only', '--error-format', 'short']
        else:
            flags.append('-fsyntax-only')
        result = run([comp.command] + flags + [isolated], tmp, timeout)
    failed = failure(result, 'compilation')
    if failed:
        return failed
    if comp.family != 'lfortran' and result.returncode == 0:
        lo, hi = bounds
        warnings = reference_warning_lines(result.output, meta.reference_warnings)
        if any(lo <= location <= hi for location in warnings):
            return Check('pass', 'diagnoses without rejection', 'compile', result.output)
    if result.returncode == 0:
        return Check('fail', 'not rejected (compiler exited successfully)', 'compile', result.output)
    if comp.family != 'lfortran':
        lo, hi = bounds
        if any(lo <= location <= hi for location in reference_error_lines(result.output)):
            return Check('pass', 'rejects', 'compile', result.output)
        return Check('fail', 'rejected without a located case diagnostic', 'compile', result.output)
    errors = lfortran_errors(result.output)
    on_line = [error for error in errors if error.first <= line <= error.last]
    if not on_line:
        return Check('fail', 'not detected on marked line', 'compile', result.output)
    tagged = any(rule in error.codes for error in on_line)
    if codes and not tagged:
        return Check('fail', f'detected without code {rule}', 'compile', result.output)
    extra = sorted((error.first, error.last) for error in errors
                   if not error.first <= line <= error.last)
    note = '' if tagged else 'detected, no rule code'
    if extra:
        note += f'; other diagnostics at {extra}'
    return Check('pass', note, 'compile', result.output)


def status(name, check, xfail):
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
    ran = {r['name'] for r in results if r['check'].outcome in ('pass', 'fail')}
    kept = [line for line in read_xfail(path) if line.split('#')[0].strip() not in ran]
    new = [f"{r['name']}  # {r['check'].note}" for r in results if r['check'].outcome == 'fail']
    Path(path).write_text('\n'.join(sorted(kept + new)) + '\n')


def safely(check, *args):
    try:
        return check(*args)
    except SuiteError as error:
        return Check('error', str(error), 'harness')


def reference_label(check, kind):
    if check.outcome == 'pass':
        if check.note == 'diagnoses without rejection':
            return 'diagnoses'
        return 'runs' if kind == 'valid' else 'rejects'
    if check.outcome == 'skip':
        return 'skip'
    if check.outcome == 'error':
        return 'error'
    if check.phase == 'run':
        return 'runtime-fail'
    if 'crashed' in check.note or 'timed out' in check.note:
        return 'crash/timeout'
    return 'rejects' if kind == 'valid' else 'unconfirmed'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-t', '--test', action='append', help='repeatable substring filter on file name or rule ID')
    ap.add_argument('--lfortran', default='lfortran')
    ap.add_argument('--std', default='f23')
    ap.add_argument('--reference', action='append', default=[],
                    help='reference compiler (repeatable), e.g. gfortran, flang')
    ap.add_argument('--reference-std', default='auto',
                    help='auto probes f2023 then f2018; an explicit mode overrides this')
    ap.add_argument('--launcher', action='append', default=[],
                    help='COMPILER=COMMAND with {images} and optional {exe}; no shell is used')
    ap.add_argument('--timeout', type=float, default=30, help='seconds per compiler or executable invocation')
    ap.add_argument('--codes', action='store_true', help='require the rule code in the diagnostic')
    ap.add_argument('--update-xfail', action='store_true')
    ap.add_argument('--coverage', help='path to doc/fortran_2023_rules.txt: print per-rule coverage')
    ap.add_argument('--report', help='write JSON results, compiler versions, and complete diagnostics')
    ap.add_argument('--list', action='store_true', help='validate and list selected files without compiling')
    a = ap.parse_args()
    if not 0 < a.timeout < float('inf'):
        ap.error('--timeout must be positive and finite')
    xfail_path = os.path.join(HERE, 'expected_failures.txt')
    xfail = {line.split('#')[0].strip() for line in read_xfail(xfail_path)}
    try:
        selected = [(path, rule, kind, metadata(path, rule)) for path, rule, kind in discover(HERE, a.test)]
        isolated = {path: list(isolated_cases(path, rule)) for path, rule, kind, _ in selected
                    if kind == 'invalid'}
        if a.list:
            for path, rule, kind, meta in selected:
                print(f'{rule:20} {kind:7} {os.path.relpath(path, HERE)} [{meta.evidence}]')
            return 0
        launchers = {}
        for value in a.launcher:
            name, separator, command = value.partition('=')
            if not separator or not name or not command.strip() or name in launchers:
                raise SuiteError('--launcher requires a unique COMPILER=COMMAND')
            launchers[name] = shlex.split(command)
        unknown = set(launchers) - {a.lfortran, *a.reference}
        if unknown:
            raise SuiteError('launcher has no selected compiler: ' + ', '.join(sorted(unknown)))
        lf = compiler(a.lfortran, True, a.std, launchers.get(a.lfortran, []), a.timeout)
        refs = [compiler(name, False, a.reference_std, launchers.get(name, []), a.timeout)
                for name in dict.fromkeys(a.reference)]
    except SuiteError as error:
        print('ERROR:', error, file=sys.stderr)
        return 2

    for comp in [lf] + refs:
        print(f'compiler {comp.command}: {comp.version}; standard={comp.standard}')
    results = []
    for path, rule, kind, meta in selected:
        base = os.path.basename(path).rsplit('.', 1)[0]
        if kind == 'valid':
            check = safely(check_valid, path, lf, meta, a.timeout)
            references = {r.command: safely(check_valid, path, r, meta, a.timeout) for r in refs}
            results.append(dict(name=base, rule=rule, kind=kind, check=check,
                                metadata=meta, references=references))
        else:
            for line, _, case, bounds, source in isolated[path]:
                check = safely(check_invalid, path, source, line, rule, bounds, lf, meta, a.codes, a.timeout)
                references = {r.command: safely(check_invalid, path, source, line, rule,
                                                bounds, r, meta, False, a.timeout) for r in refs}
                results.append(dict(name=f'{base}:{case}', rule=rule, kind=kind, check=check,
                                    metadata=meta, references=references))

    width = max(len(r['name']) for r in results)
    for result in results:
        check = result['check']
        reference = '  '.join(f'{os.path.basename(name)}={reference_label(value, result["kind"])}'
                              for name, value in result['references'].items())
        evidence = result['metadata'].evidence
        annotation = '' if evidence == 'effect' else f' [{evidence}; not full effect coverage]'
        print(f'{status(result["name"], check, xfail):5} {result["name"]:{width}}'
              f'  {reference:34} {check.note}{annotation}')
        for comp in refs:
            ref = result['references'][comp.command]
            if ref.outcome != 'pass':
                mode = f' ({comp.standard}; case needs {result["metadata"].standard})' if (
                    result['metadata'].standard and result['metadata'].standard != comp.standard) else ''
                print(f'      {comp.command}{mode}: {ref.note}')
    counts = collections.Counter(status(r['name'], r['check'], xfail) for r in results)
    print('\n' + ', '.join(f'{k}: {v}' for k, v in sorted(counts.items())))
    if refs:
        agree = sum(all(v.outcome == 'pass' for v in r['references'].values()) for r in results)
        print(f'reference compilers all agree with the test on {agree}/{len(results)} cases')
    if a.update_xfail:
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
    if a.report:
        report = {
            'compilers': [dict(command=c.command, family=c.family, standard=c.standard,
                               version=c.version, launcher=c.launcher) for c in [lf] + refs],
            'results': [dict(name=r['name'], rule=r['rule'], kind=r['kind'],
                             status=status(r['name'], r['check'], xfail),
                             check=asdict(r['check']), metadata=asdict(r['metadata']),
                             references={name: asdict(check) for name, check in r['references'].items()})
                        for r in results],
        }
        Path(a.report).write_text(json.dumps(report, indent=2) + '\n')
    return 1 if any(status(r['name'], r['check'], xfail) in ('FAIL', 'XPASS', 'ERROR') for r in results) else 0


if __name__ == '__main__':
    sys.exit(main())
