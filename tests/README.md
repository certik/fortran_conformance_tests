# Fortran 2023 conformance tests (prototype)

Tests are grouped by clause. Numbered syntax rules (`R*`) and constraints
(`C*`) normally have a valid/invalid pair:

* `<RULE>_valid.f90` exercises facets of the rule in a program that
  must compile and run with exit code 0;
* `<RULE>_invalid.f90` holds independent invalid cases, each offending
  line marked `! {error <RULE> <case>}`. Each case is compiled separately.
* `<RULE>_valid__<variant>.f90` is an additional independently compiled and
  executed program. The double underscore distinguishes a case from a
  non-standalone auxiliary source. Multi-file fixtures list their auxiliary
  sources explicitly in `fixture.json`.

For prose requirements, `S10_2_1_3_001_valid.f90` represents
`S10.2.1.3-001`. A final three-digit filename component is the suite's
local requirement number. The legacy `S15_5_2_4_invalid.f90` and its
`S15.5.2.4` markers remain supported; the design explains its corrected
source reference.

Design, conventions and the plan for filling this in are in
`doc/fortran_2023_conformance_tests.md`; the rules are in
`doc/fortran_2023_rules.txt`.

`doc/fortran_2023_S10_2_1_3.md` displays the 32 intrinsic-assignment S
requirements. Their first executable batch contains 41 programs: 35 effect
cases, three positive controls for program restrictions, and three
context-only cases for the undefined-result requirement. It declares
assertions for 138 of the catalogue's 144 named facets; the six deliberate
omissions are listed there and enforced by the corpus regression tests.
This is authored coverage, not a claim that every facet has executed or
passed.

The two additional numbered constraints are C601 (name length) and C1401
(PROGRAM/END PROGRAM names): five valid programs and ten isolated invalid
cases. The later readiness calibration adds out-of-band fixtures for C
interoperability, fixed-form source, EOF rejection, and termination/I/O.
The full rollout plan is `doc/whole_standard_plan.md`.

## Running

The runner uses Python 3.9+ and its standard library on POSIX systems.

```
# build/src/bin first on PATH, then:
tests/run_tests.py                                   # LFortran only
tests/run_tests.py --reference gfortran --reference flang
tests/run_tests.py -t S10.2.1.3 -t C601 -t C1401        # repeatable filters
tests/run_tests.py --list -t S10.2.1.3                # no compiler invocation
tests/run_tests.py --codes                           # require rule codes
tests/run_tests.py --update-xfail                    # regenerate expected_failures.txt
tests/run_tests.py --coverage doc/fortran_2023_rules.txt
tests/run_tests.py --report /tmp/fortran-conformance-results.json
python3 -B -m unittest discover -s tests -p 'test_*.py'
```

Requirements and pending facets are now authored in the JSON catalogues
listed by `doc/catalogues/index.json`. Regenerate the Markdown definition
regions and run the generic audit with:

```
python3 tests/suite_data.py --render
tests/run_tests.py --audit
tests/run_tests.py --audit --require-complete-source
```

The ordinary audit checks catalogue/case consistency and current fixture
approvals without invoking compilers. Full-source closure is a separate,
deliberately stricter gate. The pinned PDF census includes unprocessed
sections, so they cannot disappear from the denominator. Detailed
table/list subdivisions and independent visual review remain necessary.

Even a section containing only already-numbered R/C items needs an explicit
reviewed catalogue for final closure. Catalogue review is bound to the
catalogue contents and the corresponding source census, including fine
subdivisions and their dispositions:

```
tests/run_tests.py --record-catalogue-review SECTION \
    --review-rationale 'Original source and every scoped unit independently reviewed.'
```

Changing those inputs makes the catalogue review stale. This source-review
operation is separate from fixture approval and cannot be combined with an
xfail update. It does not ratify the entire PDF census.

Every compiler and executable invocation has a 30-second timeout,
configurable with `--timeout`. A timeout terminates the invocation's process
group. Compilation crashes and ASR-verifier failures are failures, not
successful language diagnostics. Failure to start a tool is a harness
`ERROR`, which cannot be hidden by an xfail.

Reference mode defaults to `--reference-std auto`: probe `f2023`, then
`f2018`, and display the actual mode and version. An explicit
`--reference-std f2018` reproduces the earlier reference mode. Rejection of
an F2023-only case in F2018 mode is not proof that the fixture is invalid.
Reference results never override LFortran's result.

The JSON report contains versions, modes, metadata, fixture fingerprints
and reviews, verdicts, and diagnostics. Manifest fixtures record separate
compile/link/run commands and staged input hashes. Reports are artifacts,
not expected-output files.

Compiler versions and input/requirement fingerprints are checked again
before a report or baseline update. Detected changes make the observations
provisional and prevent an xfail update. Use frozen compiler installations
for long batches; a version string cannot detect every uncommitted change
to an installation being rebuilt concurrently.

## Case metadata

Place metadata in the leading comment block:

```fortran
! rule: S10.2.1.3-017
! covers: hexadecimal real-destination destination-kind
! profile: ieee-binary
! standard: f2023
```

`rule` must agree with the filename; catalogue cases also require `covers`,
a space-separated list of named facets from their definition. Coverage is
credited only to that explicitly annotated requirement, not automatically
to dependencies mentioned in the source.

| Header | Meaning |
| --- | --- |
| `evidence: effect` | Direct runtime assertions or diagnostic observations; retain case kind and execution phase |
| `evidence: positive-control` | Conforming controls; not a check that violating programs are diagnosed |
| `evidence: context-only` | Context/admission evidence, not a direct assertion about an undefined value |
| `profile: ...` | Required optional processor properties, checked before compiling the case |
| `requires: coarray` | Enable the compiler's coarray mode; lack of implementation is not an optional-profile skip |
| `images: 2` | Compile the case, then require a configured two-image launcher to execute it |
| `standard: f2023` | Mark a case needing F2023 features so reference-mode limitations remain visible |
| `reference-warnings: long-names` | Explicit diagnostic-code allowance for references, not for LFortran |
| `oracle-basis: lfortran-policy` | An explicitly additional diagnostic expectation |
| `oracle-basis: processor-profile` | An expectation qualified by the named `oracle-profile` |

Profiles live in `tests/profiles/` and are not discovered as conformance
cases. Their names are discovered from the files rather than hard-coded
in Python. Their result is cached
per compiler for the run. Only a profile executable's exit code 77 denotes
an unavailable optional property. A failed or crashing probe is a failure;
it is never converted to a successful skip. Exit code 77 from an ordinary
test is also a failure.

The `ieee-binary` profile checks IEEE support and the default-real/binary32
and double-precision/binary64 model before compiling representation-specific
BOZ literals. Unsupported kinds are not replaced with a default kind while
silently claiming the missing facet.

## Out-of-band and multi-file fixtures

`tests/fixtures/*/fixture.json` declares inputs without annotating the
Fortran text. The four readiness fixtures exercise:

| Fixture | Contract |
| --- | --- |
| `c_interop` | Ordered Fortran-module, C, and caller compilation followed by separate linking |
| `fixed_form` | Exact column-sensitive CRLF bytes, with external metadata |
| `missing_end` | Unterminated source with no final newline and an external EOF diagnostic predicate |
| `stop_io` | Stdin, stdout, a generated file, and profiled normal exit status 200 |

Every asset must be declared. Unknown fields, escaping paths, undeclared
files, invalid dependencies, and input/output collisions are errors. Build
steps are typed operations, not arbitrary shell commands. `--cc` selects
the C companion compiler; linking normally uses the Fortran driver.

`expect.phase` is `compile`, `link`, or `run`. Expected compile failure
names its step; an earlier failure cannot satisfy a later expectation.
Rejection requires a real diagnostic, not a crash. External expectations
can name a source line, file, or EOF anchor.

For a reporting requirement that does not mandate fatal rejection, opt in
with `expect.outcome: "diagnose"` in a compile-only fixture. It is an
invalid-input case, not a conforming compile-only control. The diagnostic
must name a declared input file and an exact line; an error at that location
can satisfy the expectation regardless of ordinary process exit status.
Nonfatal reports require explicit compiler-family, severity, and
case-insensitive message-substring predicates:

```json
{
  "phase": "compile",
  "step": "source",
  "outcome": "diagnose",
  "diagnostic": {
    "file": "source.f90",
    "line": 6,
    "allow_nonfatal": [
      {"compiler": "flang", "severity": "portability", "contains_any": ["missing space"]}
    ]
  }
}
```

`allow_nonfatal` supports `warning` or `portability` and the `lfortran`,
`gfortran`, `flang`, or `c` compiler families. Optional top-level
`diagnostic.contains_any` further restricts every matching diagnostic.
Predicates match the located diagnostic message, not source echoes or
other output. A wrong file/line, unlocated message, unrelated warning,
earlier build failure, crash, verifier failure, or timeout cannot pass.
`--codes` still requires the LFortran rule reference when requested.
The existing `reject` outcome and ordinary isolated-negative rejection
policy are unchanged; no arbitrary warning allowance is added to them.
Successful compile-only and link-only references are displayed as
`compiles` and `links`, never as runtime observations.

Runtime expectations use an exact exit code. Nonzero codes need an
explicit policy/profile basis: Fortran does not universally mandate the
STOP-code-to-process-status mapping. Signals and timeouts cannot satisfy
a normal status-200 expectation. Compiler failure detection is separate
from application termination.

Text stdout/stderr and generated-file oracles accept one string or an
explicit list of alternatives. `expect.file_matches` compares generated
bytes with an immutable declared fixture input, not a possibly modified
staged copy. Stdin is supplied as bytes; invalid UTF-8 cannot silently
satisfy a text oracle.

`.gitattributes` disables fixture line-ending conversion. Staging copies
and verifies bytes, with their hashes in the report. The fixed-form source
is intentionally a binary Git diff so its CRLF records are not mistaken
for trailing-whitespace errors.

## Isolated negative cases

New invalid files use explicit boundaries:

```fortran
! rule: C1401
! case: mismatched-name
program first
    implicit none
end program other ! {error C1401 mismatched-name}
! case: named-without-program
    implicit none
end program missing ! {error C1401 named-without-program}
```

The runner blanks out other cases, retains shared setup, and preserves line
numbers. Each boundary needs exactly one marker with the matching case ID.
This permits several main-program cases, missing-END cases, and fixed-form
cases without depending on compiler recovery. Legacy free-form files use
their column-1 top-level END statements as boundaries; unmarked helper
units remain in each compilation.
Reports retain the isolated input hash and actual compiler command,
return code, and streams, as they do for manifest fixtures.

LFortran must exit unsuccessfully without a compiler crash/verifier failure
and issue an error whose source range includes the marked line. `--codes`
additionally requires the rule reference, either in the legacy `[C801]`
field or in a rendering such as `[E0231] (F2023 C801)`. Other diagnostics
are retained for review, but cannot substitute for the marked diagnostic.
`--continue-compilation` is no longer needed or passed.

References normally corroborate an invalid case with a nonzero exit and
an error within that case. C601 explicitly also permits the reference
diagnostic `[-Wlong-names]`: Flang reports this as a portability diagnostic
without rejecting the program. Such a result is displayed as `diagnoses`,
not `rejects`. Arbitrary warnings cannot corroborate a case, and LFortran's
error/rejection requirement is unchanged.

## Coarray execution

Without a launcher, GNU Fortran uses `-fcoarray=single`; Flang uses
`-fcoarray`, and LFortran uses `--coarray`. The local coarray-component
and same-image team cases have conforming single-image executions.
The cross-image case instead requires two images and is explicitly
`SKIP` after successful compilation if no launcher is configured.

The library-backed two-image path has now been exercised with GNU 14.4.0,
MPICH 4.3.2, and OpenCoarrays 2.10.3. `tools/calibration/` contains an
isolated, locked setup; no shared compiler or SDK environment was changed.

For an existing OpenCoarrays installation, a targeted reference run can use:

```
tests/run_tests.py -t S10_2_1_3_023_valid__cross_image \
    --reference caf --launcher 'caf=cafrun -n {images} {exe}'
```

A `caf` compiler wrapper controls its library/link flags. For a GNU compiler
with a configured launcher, the runner selects `-fcoarray=lib`; the chosen
compiler wrapper must supply the runtime libraries. Launcher commands are
argument vectors, not shell scripts; `{images}` and `{exe}` are substituted,
and the executable is appended if `{exe}` is omitted.

Even a successful cross-image context case does not establish a particular
undefined opaque value. It checks only the ordinary payload and never reads
the copied C_PTR, C_FUNPTR, or TEAM_TYPE components.

## Fixture approval is not a compiler verdict

`tests/reviews.json` records adjudications by fixture review key. Each
ordinary valid file, invalid container, or manifest fixture has one key.

| State | Meaning |
| --- | --- |
| `unreviewed` | Not approved |
| `source-reviewed` | Approved with a source rationale, without claiming successful reference execution |
| `reference-validated` | Approved with fingerprint-matched reference evidence for every execution in the fixture |
| `disputed` | Interpretation or fixture remains unresolved |
| `needs-oracle` | No defensible oracle yet |
| `stale` | Inputs, a profile, or the requirement changed after adjudication |

The initial migration has 65 reference-validated fixtures and four
source-reviewed-only fixtures: the two enum programs, the allocated-coarray
component case, and the additional C1302 diagnostic-policy packet.
Their rationales and disagreements remain visible. Approval never changes
a compiler failure into a pass.

Draft observation and explicit approval are separate operations:

```sh
tests/run_tests.py --allow-unreviewed --reference-only \
    --reference gfortran --reference flang -t RULE --report observations.json
tests/run_tests.py --record-review FIXTURE_KEY \
    --review-state reference-validated \
    --review-rationale 'Source and oracle reviewed; the observations corroborate them.' \
    --review-report observations.json
```

For `source-reviewed`, supply a specific source rationale and use
`--review-source` for additional anchors. A compiler failure is not an
approval rationale. Missing observations, stale/wrong fingerprints, and
provisional reports cannot establish reference validation.

Unapproved fixtures prevent normal successful runs and cannot be hidden
by existing XFAILs. `--allow-unreviewed` is observation mode only and is
incompatible with `--update-xfail`. The latter refuses unapproved fixtures
before modifying the baseline.

`--reference-only` runs without LFortran or its xfail list. `--no-skips`
requires actual results in calibration configurations that must execute.

## Expected failures and coverage

Only observed failures are recorded by `--update-xfail`. Filtered-out,
skipped, and harness-error entries are preserved rather than silently
removed. The update command still returns the pre-update verdict; run again
to check the new baseline. Review fixtures and reference disagreements
before updating it.

`PASS`, `XFAIL`, and exit code 0 describe the selected run, not full-standard
conformance. `--coverage` reports case inventory and outcomes, not complete
facet coverage. Positive controls, context-only cases, optional-profile
skips, and unexecuted multi-image cases remain distinct. Compiler/reference
observations and the remaining S facets are recorded in the catalogue.
