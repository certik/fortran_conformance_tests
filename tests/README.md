# Fortran 2023 conformance tests (prototype)

Tests are grouped by clause. Numbered syntax rules (`R*`) and constraints
(`C*`) normally have a valid/invalid pair:

* `<RULE>_valid.f90` exercises facets of the rule in a program that
  must compile and run with exit code 0;
* `<RULE>_invalid.f90` holds independent invalid cases, each offending
  line marked `! {error <RULE> <case>}`. Each case is compiled separately.
* `<RULE>_valid__<variant>.f90` is an additional independently compiled and
  executed program. The double underscore distinguishes a case from a
  planned auxiliary source named `<RULE>_valid_<suffix>.*`.

For prose requirements, `S10_2_1_3_001_valid.f90` represents
`S10.2.1.3-001`. A final three-digit filename component is the suite's
local requirement number. The legacy `S15_5_2_4_invalid.f90` and its
`S15.5.2.4` markers remain supported; the design explains its corrected
source reference.

Design, conventions and the plan for filling this in are in
`doc/fortran_2023_conformance_tests.md`; the rules are in
`doc/fortran_2023_rules.txt`.

`doc/fortran_2023_S10_2_1_3.md` defines the 32 intrinsic-assignment S
requirements. Their first executable batch contains 41 programs: 35 effect
cases, three positive controls for program restrictions, and three
context-only cases for the undefined-result requirement. It declares
assertions for 138 of the catalogue's 144 named facets; the six deliberate
omissions are listed there and enforced by the corpus regression tests.
This is authored coverage, not a claim that every facet has executed or
passed.

The two additional numbered constraints are C601 (name length) and C1401
(PROGRAM/END PROGRAM names): five valid programs and ten isolated invalid
cases. No additional R/C rules were added in this batch.

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

The JSON report contains versions, modes, case metadata, verdicts, and
complete diagnostic output. It is a run artifact, not an expected-output
file; choose an appropriate artifact location.

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
| `evidence: effect` | Default: assertions about conforming execution |
| `evidence: positive-control` | Conforming controls; not a check that violating programs are diagnosed |
| `evidence: context-only` | Context/admission evidence, not a direct assertion about an undefined value |
| `profile: ...` | Required optional processor properties, checked before compiling the case |
| `requires: coarray` | Enable the compiler's coarray mode; lack of implementation is not an optional-profile skip |
| `images: 2` | Compile the case, then require a configured two-image launcher to execute it |
| `standard: f2023` | Mark a case needing F2023 features so reference-mode limitations remain visible |
| `reference-warnings: long-names` | Explicit diagnostic-code allowance for references, not for LFortran |

Profiles live in `tests/profiles/` and are not discovered as conformance
cases. Available profiles are `two-integer-kinds`, `two-logical-kinds`,
`integer-range-nine`, `iso10646`, and `ieee-binary`. Their result is cached
per compiler for the run. Only a profile executable's exit code 77 denotes
an unavailable optional property. A failed or crashing probe is a failure;
it is never converted to a successful skip. Exit code 77 from an ordinary
test is also a failure.

The `ieee-binary` profile checks IEEE support and the default-real/binary32
and double-precision/binary64 model before compiling representation-specific
BOZ literals. Unsupported kinds are not replaced with a default kind while
silently claiming the missing facet.

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
