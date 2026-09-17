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

Source dispositions include `requirements`, `definition`, `permission`,
`recommendation`, `informative`, `structural`, and `unresolved`.
`recommendation` records advisory normative text with a required rationale.
It can close a classification gap without creating mandatory requirements,
test cases, or a claim that a processor implements the advice. Assessing
actual documentary adherence requires separate, qualified evidence.

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
group. Pipe draining and process reaping have separate bounded cleanup
allowances, at most one second each. A pipe held outside the child group
cannot make the post-timeout drain wait indefinitely; captured partial
stdout/stderr bytes are retained. Compilation crashes and ASR-verifier failures are failures, not
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

A supplementary S-owned `category: effect` requirement may explicitly
declare source-supported admission/control facets:

```json
"facets": ["result", "confirmation"],
"positive_control_facets": ["confirmation"]
```

`positive_control_facets` is optional. When present it must be a nonempty,
unique list of nonempty strings naming existing facets, and is permitted
only on supplementary effect requirements. It is not available for
numbered R/C requirements or other categories. Without it, the existing
role rules are unchanged: valid S-effect cases require `evidence: effect`.

Every listed facet requires a **valid positive-control** case; it cannot
be labelled `effect` or `context-only`. Unlisted S-effect facets still
require `effect`. One case cannot mix facets requiring incompatible roles,
and an invalid case cannot cover a listed control facet, even with an
additional diagnostic-policy basis. Within an opted-in requirement, an
invalid case on unlisted facets still requires `effect` and its original
diagnostic basis; policy does not bypass the facet's role. Compile, link
and run controls retain their actual declared phase. A successful run/positive-control remains in
the positive-control cohort and never contributes `runtime_effect_pass`.

The designation needs independent source review; adding it does not
approve a source, case or inventory. It appears in generated definitions
and is part of the existing complete requirement/source fingerprint
material, so adding or changing it stales dependent adjudications.
Declaring a control facet does not author a case, clear its pending plan,
prove its oracle or supply an observed pass. Authored facet counts, case
roles, qualified observations, source review and global coverage remain
separate.

Profiles live in `tests/profiles/` and are not discovered as conformance
cases. Their names are discovered from the files rather than hard-coded
in Python. Their result is cached
per compiler for the run. Only a profile executable's exit code 77 denotes
an unavailable optional property. A failed or crashing probe is a failure;
it is never converted to a successful skip. Exit code 77 from an ordinary
test is also a failure.
Reports include profile compile/run traces, input hashes and cached
outcomes in `profile_checks`, separately from the case's own execution.
An unavailable compound profile does not identify which individual
property failed unless the probe itself reports that information.

The `ieee-binary` profile checks IEEE support and the default-real/binary32
and double-precision/binary64 model before compiling representation-specific
BOZ literals. Unsupported kinds are not replaced with a default kind while
silently claiming the missing facet.

The legacy `S15.5.2.4` argument-kind cases retain their negative execution
IDs but use separate `legacy_argument_*` manifests. Their real, integer,
logical and character kind premises are independently gated; default
REAL kind 4 is required only for the three default-literal cases. The
character branch additionally qualifies kind 4 as ISO 10646 so its literal
is representable. No profile compiles the invalid call as its own probe.
Each negative retains its explicit LFortran rejection-policy basis and
has a matching compile-only repair, not a claimed runtime effect.
`tools/generate_legacy_argument_kind_fixtures.py --check` verifies the
deterministic inputs.

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

A C build step can request `"fortran_binding_header": true` for
`ISO_Fortran_binding.h`. The runner queries the selected Fortran processor,
not a globally chosen CPATH header: LFortran's advertised C include directory,
GNU's include directory, or Flang's resource/install prefix. Only the
selected header is copied into a private include directory for that C step;
GNU's standard headers cannot shadow the companion's headers through this
mechanism. Fixture inputs/outputs cannot replace the processor header.
Missing or ambiguous discovery is a harness error, not an optional feature
skip. Processor-specific header dependencies beyond the staged header must
be resolved explicitly rather than guessed from another compiler.

Header path, hash, discovery method and available version-macro text are
recorded in compiler/case observations. The original header is rechecked
before staging and at snapshot confirmation; changed resources invalidate
the run. Reference adjudication of a descriptor fixture requires this
header provenance and the C companion identity. A successful link or a
matching version banner does not establish ABI compatibility, and a
descriptor/header version disagreement remains a failed interface check.

`expect.phase` is `compile`, `link`, or `run`. Expected compile failure
names its step; an earlier failure cannot satisfy a later expectation.
Rejection requires a real diagnostic, not a crash. External expectations
can name a source line, file, or EOF anchor.

For a reporting requirement that does not mandate fatal rejection, opt in
with `expect.outcome: "diagnose"` in a compile-only fixture. It is an
invalid-input case, not a conforming compile-only control. The diagnostic
must name a declared input file and a line; an error at that location
can satisfy the expectation regardless of ordinary process exit status.
Optional `diagnostic.end_line` declares a closed statement span. When it
is supplied, a reported point or range must fit entirely within that span;
a whole-program recovery range merely intersecting it does not pass.
A specifically reviewed span may include a compiler's one-past-final-record
EOF position. This does not invent another physical source record or
authorize unlocated scan/parse summaries.
Without `end_line`, a point is exact: a multi-line recovery range merely
enclosing it cannot pass. Compile-phase `reject` manifests also support
an explicitly declared span while retaining their rejection requirement.
A relational rule such as matching PROGRAM/END names can declare both
endpoints and require a name-mismatch message. That qualified relation is
not permission to accept arbitrary whole-unit recovery ranges.
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
`gfortran`, `flang`, or `c` compiler families. Instead of `contains_any`,
`equals_any` matches a complete diagnostic message, case-insensitively.
Each nonfatal predicate must choose exactly one of those message forms.
Optional top-level
`diagnostic.contains_any` further restricts every matching diagnostic.
For `diagnose`, optional `diagnostic.excludes_any` rejects a candidate
message containing any of its nonempty case-insensitive substrings. The
C1514 length-only pair uses this to exclude unsupported/unimplemented
feature reports even when they mention ambiguity. This is opt-in;
unrelated fixture predicates and fingerprints are unchanged.
Predicates match the located diagnostic message, not source echoes or
other output. A wrong file/line, unlocated message, unrelated warning,
earlier build failure, crash, verifier failure, or timeout cannot pass.
Native compiler `Internal:` errors also fail before a matching cause is
considered, including LFortran's short `file:first-last:columns` format.
This does not require each fixture to repeat that exclusion. Warning
messages, quoted examples, source echoes and application runtime output
remain distinct; the first unshielded location still governs extraction.
The short-format severity is a header phrase, not a search through the
message: a quoted error example after a note or warning delimiter cannot
be reclassified as the outer diagnostic's severity.
Both the native failure guard and diagnostic extraction use that same
first-unshielded-header check. Severity normalization accepts the same
space/tab separators as the header grammar; quoted inner locations cannot
borrow the expected filename or statement marker.
Complete quoted examples in recognized unlocated diagnostic, note, remark
and help messages are likewise content, including driver-prefixed messages.
Unquoted coordinates in severity-like filenames retain their existing
location interpretation.
`--codes` still requires the LFortran rule reference when requested.
The existing `reject` outcome and ordinary isolated-negative rejection
policy are unchanged; no arbitrary warning allowance is added to them.
Successful compile-only and link-only references are displayed as
`compiles` and `links`, never as runtime observations.

For an explicitly declared diagnostic input, native `file:line:column`
and `file:line:first-column-last-column` headers are recognized
independently of the filename suffix, including
`.inc`, other suffixes and extensionless included assets. Relative directory
components in the expected filename remain significant. Include-context
records cannot lend their locations to a later unlocated error, and a
host-file location is not substituted for an included-file expectation.
Column ranges describe one source line, not a line span; their endpoints
must be positive and ordered. A malformed location-like header clears any
earlier attribution, even when its column syntax cannot be parsed.
The legacy unbound parser retains its filename-suffix restriction and
applies the same location validation. Legitimate source/caret continuation
records and native single-column-zero headers remain supported. Native
source/caret records are classified before header detection, so their
expressions and comments remain content. Complete, delimited quoted text
inside diagnostic/driver messages is also shielded from header detection.
An unquoted coordinate sequence is not shielded merely because a filename
resembles a severity or driver prefix, as in `Error:9:1:` or
`Error:asset:9:1:`. Ambiguous unquoted location/message records cannot
borrow an earlier location or preserve single-source-driver attribution.
This is a conservative text-format qualification, not a prohibition on
extensionless or severity-named assets; original output is retained.
Classification and extraction must select the same first unshielded
coordinate. A mixed record cannot be classified using one coordinate and
then qualify an earlier quoted coordinate or skip a malformed first
candidate to a later valid one. Filename namespaces that collide with
native source-record delimiters need disambiguating path/record provenance
or separate format qualification; this parser does not certify every
legal filesystem namespace.

The GNU driver form `f951: Warning: MESSAGE in line N` has no filename.
It can be qualified explicitly with a nonfatal predicate containing
`"attribution": "single-source-driver"` and `equals_any`. This route is
limited to one declared ASCII input, one Fortran compilation step, an
explicit free source form, a lower-case `.f`/`.f90` suffix, and no INCLUDE
spelling anywhere in that input. The predicate must specify `gfortran`
and `warning`. Competing source locations and malformed location-like
headers disqualify this attribution.
The separately parsed line number must still match the declared location,
and only the exact message is accepted; other driver messages do not pass.
The source hash, command and original output remain in the report, with
the inferred attribution identified in the result note. Ordinary located
reports remain the default.

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

An adjacent `<RULE>_invalid.cases.json` can give a retained container
per-execution contracts without moving its source or changing execution
IDs. It contains `schema_version: 1` and a `cases` object whose keys exactly
match every original marker name. Each entry supplies its own `facets`,
`outcome: "diagnose"`, and `diagnostic.contains_any`; optional
`diagnostic.excludes_any` excludes known wrong causes. An optional `profiles`
list explicitly replaces the inherited file-level list. The initial
sidecar contract deliberately supports only compile-phase reporting,
without generic warning or driver-attribution fallbacks.

The diagnostic filename and default point come from the original source
and marker. An explicit `line`/`end_line` relation must contain that marker
and stay within the preserved source. The source bytes and isolation rules
are unchanged. Each execution then has its own review key and a fingerprint
binding the full source, effective metadata and its exact diagnostic
contract. A sidecar cannot assign a union of all facets to every isolated
case; unknown/missing cases, profiles and orphan contracts are errors.
Changed contracts require fresh adjudication. Source-specific predicate
validity still requires independent review rather than compiler consensus.

Without a per-execution `diagnose` contract, LFortran must exit
unsuccessfully without a compiler crash/verifier failure
and issue an error at the exact marked line. A multi-line statement needs
an explicitly declared manifest span; an unqualified recovery range cannot
stand in for the point. `--codes`
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

## Finite canonical case links (bounded prototype)

The optional index field `evidence_links` names one repository-relative
JSON registry, currently `doc/evidence/canonical_case_links.json`. It
contains `schema_version: 1`, the exact index `standard` pin, and `links`.
These records are not fixtures and are never discovered as executions.

| Link field | Contract |
| --- | --- |
| `id` | Unique explicit identifier; no selectors |
| `target` | Exactly `requirement`, `facet`, `source_units`; a known supplementary S requirement, one declared facet and nonempty qualified anchors belonging to that requirement |
| `basis` | Nonempty, unique `section#unit` anchors in the pinned census or its declared subdivisions |
| `claim`, `limitation` | Nonempty finite semantic claim and its boundary |
| `pattern` | Optional for legacy R/C pairs; otherwise explicit `diagnostic-control`, `runtime-effect`, or `positive-control` |
| `cases` | Exact members for the pattern, each with `id`, `role`, `primary_rule`, `source`, `path`, `phase` |
| `review` | Optional existing-style `state`, `rationale`, `sources`, `fingerprint` adjudication; absent means draft/unreviewed |

Each member names an actual canonical R/C or S execution ID and its exact
repository-relative source/manifest path. The primary rule must differ from
the target requirement. An R/C member uses its numbered source anchor; an
S member uses an anchor belonging to its own requirement and requires an
explicit `pattern`. The member anchor must be in `basis`.

The default `diagnostic-control` pattern retains exactly one compile-phase
`diagnostic` and one explicit `positive-control` with the same primary
rule. `runtime-effect` requires exactly one valid run-phase effect case;
`positive-control` requires exactly one valid case already classified as a
positive control, at its original phase. A compile control cannot become
a runtime effect through a link. Each connection needs independent source
review: internal allowed use, for example, does not establish outside
inaccessibility merely because a target facet concerns privacy.

A target facet listed in `positive_control_facets` requires the explicit
`positive-control` pattern. Neither a runtime-effect link nor a
diagnostic/control pair can promote other evidence into that control
facet. Canonical S-owned marked controls can be reused only with their
actual positive-control role and phase; mixed-role cases cannot bypass
the direct-case rules through a link. Unmarked targets retain the
existing pattern contracts.

Declared phases must match the original case contract. Additional
diagnostic-policy oracles cannot be imported through a link. Paths, IDs
and roles cannot repeat within a record. Unknown fields (including
duplicate JSON keys), anchors, facets, members, noncanonical/escaping paths
and self-reuse are errors. Links cannot stand in for actual directly owned
cases or provide circular case approval. These finite patterns do not add
numbered-wrapper, arbitrary documentary, use-graph or aggregate contracts.

A facet has either direct authored cases or one link, not both. Pending
facets must exactly match the remainder. Removing a link without restoring
pending or direct coverage is an error. `authored_facets` remains the
**direct** count; `linked_facets` and `current_linked_facets` are separate.
No link adds a compiler execution, direct passing facet or runtime effect.
Filters do not follow links: selecting an S requirement does not secretly
execute its canonical members, and selecting a canonical member does not
create a second S result.

Link adjudication fingerprints bind the complete link (excluding its own
review), the target definition, pin and source-unit material, relevant
catalogue fingerprints/reviews, each canonical input/metadata/profile/
requirement fingerprint, its fixture execution set and its current
adjudication. Changes or removals cannot retain current linked coverage.
Already-catalogued source sections need current source reviews. Uncatalogued
canonical source units are reviewed narrowly through the declared basis;
that does not approve an entire uncatalogued subclause or the global census.

The independent parent workflow is **source review, fixture observation
and approval, then semantic link adjudication**. The first two operations
do not require an approved link. After inspecting original source and the
current finite observations, the parent can explicitly record the connection:

```sh
tests/run_tests.py --record-evidence-review \
    S7.2-003.length-only-overload-exclusion --review-state source-reviewed \
    --review-rationale 'Independently reviewed the finite source connection and its premises.'
```

This operation writes only the evidence registry. It requires approved,
current canonical fixtures and current relevant source reviews, and
automatically records all declared target/basis anchors. It accepts no
compiler report as semantic authority. `reference-validated` is not a link
review state. Referenced fixture reference validation must contain a
successful observation for the actual required phase and a supported
standard mode; compile success cannot validate a runtime case, nor can
an F2018 rejection validate an F2023-only diagnostic. Source-only approvals
remain possible, explicitly without claimed reference corroboration.

An absent review yields `draft` with an `unreviewed` review; explicit
`unreviewed`, `disputed` and `needs-oracle` states remain blocked. Changed
content or prerequisites yields `stale`; an independent current
`source-reviewed` adjudication yields `current`. Successful compiles never
change these states. Ordinary audit requires all links current; normal
selected runs and baseline updates enforce relevant links. Observation
mode `--allow-unreviewed` preserves draft/stale status and cannot update a
baseline. Even with that option, whole-source closure cannot bypass the
link gate.

`--list` and coverage output show finite links separately. JSON
`evidence_links` joins observations by exact primary case ID, preserving
compiler identity, mode, phase, failure/skip notes and `not-selected`
members; complete traces remain on the original result. In reference-only
reports there is no synthetic target observation. Linked observed/passing
aggregation is **not implemented**, explicitly `not-computed`, even for
a current semantic link. A source-only approved link can coexist with
failed or missing compiler evidence without making that evidence pass.

## Finite whole-suite execution ledgers (observational prototype)

The optional `execution_aggregates` index entry names
`doc/evidence/whole_suite_execution.json`. Its `schema_version`, exact
`standard` pin and `aggregates` array define a separate kind of evidence.
Each aggregate has an `id`, supplementary-effect `target` with source
anchors, `basis`, `claim`, `limitation`, and optional source `review`.
This first contract accepts only `scope: "all-collected-cases"` and
`coverage_credit: "none"`. It cannot name a filtered subset or clear its
target's pending facet.

The current collected suite is enumerated in full, not inferred from the
selected invocation. Every ID, primary requirement, source/manifest path,
declared phase, metadata, actual input/profile hash, requirement fingerprint,
fixture execution group and current adjudication enters the inventory
binding. The source census and all registered catalogue fingerprints/review
states are also bound. Adding, removing or changing even an unselected case
makes the aggregate review stale. Changes during a report or baseline run
make the observations provisional and prevent baseline modification.
Every member's actual fingerprint is checked before grouping reviews.
Different inputs with the same review key are errors, even when their
execution IDs differ or one member is unselected. Legitimate isolated
executions from the same source container still share a review.

Review the relevant source, all current fixture adjudications and the
finite inventory before recording its independent source adjudication:

```sh
tests/run_tests.py --record-execution-review \
    S4.2-001.whole-suite-execution --review-state source-reviewed \
    --review-rationale 'Independently reviewed the finite inventory and its qualifications.'
```

A compiler report cannot perform this adjudication. Reference-validated
member approvals must themselves contain an observation at the required
phase and supported standard mode. Source-only member approvals remain
possible without claiming reference corroboration. Normal audit, runs and
baseline updates require registered aggregates to be current;
`--allow-unreviewed` permits draft observations but never baseline updates.

**Inventory review is not member approval.** A current, explicit
`needs-oracle` or `disputed` adjudication may remain in a reviewed inventory,
listed under `members_needing_approval` with `all_members_approved: false`.
It cannot produce a qualified pass, receive an xfail update, or satisfy
normal whole-suite audit/run gates. Unreviewed or stale member adjudications
still block inventory review, as does a falsely labelled reference
validation lacking the required phase/mode. Independently approved
selections can continue to be observed and baselined without hiding or
removing the unresolved member from the full denominator.

JSON `execution_aggregates` joins each compiler's observations by exact
case ID, retaining unselected members as `not-selected`. It never launches
another test or synthesizes a target from reference-only results. Different
compiler versions, modes, launchers and header configurations are not joined
into one successful processor. XFAIL status is not a passing outcome, and a
generic resource error is not evidence of a permitted size or complexity
limit.

Each compiler has separate populations for runtime effects, non-runtime
effects, positive controls, context-only cases and invalid-input diagnostics.
The latter are outside the declared-valid execution population, not erased
from the inventory. Counts are **cases**, not inferred passing facets.
An admission control can pass its declared compile/link/run expectation
without becoming an interpretation effect. A context-only run does not
establish an undefined value.

`qualified_pass` means the declared-valid case passed with a current
aggregate/case adjudication, matching inputs, the declared observed phase
and successful trace, a qualifying standard mode, successful declared
profile traces/hashes, and the required recorded launcher/companion/header
evidence. It is not independent certification of processor limits, external
interfaces, ABI compatibility or universal execution semantics. An explicit
profile-qualified application exit such as 200 is judged against its
declared runtime status, not mistaken for a compiler crash.

The bound execution plan retains the ordered build steps, link driver,
terminal expectation, arguments and stdin asset. Each check records its
versioned `execution_context`, including the private workspace and any
staged compiler resources. Shared command constructors reconstruct every
expected argv from that declaration and the recorded configuration.
The entire observed prefix, exact phase/step order, preceding successes,
source/output paths, effective compiler flags, and built-executable/run
relationship must agree. Profiles likewise bind one ordered compilation/run
pair to their actual source, hash, compiler and executable.

The report's `source_root` connects the declared repository-relative inputs
to the observed commands; it is invocation provenance, not part of portable
fixture or inventory review fingerprints. Launcher/wrapper shapes are
validated, and actual run commands must contain the configured executable,
image substitution and arguments. A C link driver needs a recorded C
companion even when there are no C compilation steps. Header evidence must
have a matching C build and private include path. Input hashes have an exact
declared key set, plus only the processor resources used by that execution.
Declared stdin is hashed from the actual bytes supplied to the process and
joined to the corresponding input asset.

Contradictory or incomplete success traces, transplanted compiler/profile
observations, missing required interface identities and unrelated input
claims are consistency errors: the report becomes provisional and no xfail
update is permitted. Genuine earlier compiler failures, unavailable
profiles, missing launchers and correctly labelled older-standard
observations remain failed, skipped or mode-unqualified evidence instead.
This is internal evidence consistency, not cryptographic attestation or an
inventory of all transitive operating-system and compiler dependencies.

`runtime_attempted` comes from a recorded run command; an early compilation
failure cannot become a run effect. `runtime_effect_pass` additionally
requires a qualified pass in the runtime-effect population. Missing,
failed or skipped profiles, unsupported standard modes and provisional
observations cannot produce qualified passes. Complete traces and output
oracles remain on the primary result, with aggregate rows retaining its
exact ID and input evidence.

`observation_set_complete` describes row presence for the whole collected
population; `valid_observation_set_complete` describes the declared-valid
population. Neither means that programs executed or passed: present failure
and skip observations remain present. Even
`all_declared_valid_expectations_qualified` concerns only the finite
declared phases, including admission controls, not the universal
processor obligation.

Audit counts `observational_aggregates` and
`current_observational_aggregates` remain separate from direct or linked
authored facets. No new case or completion credit is assigned to S4.2-001.
Its source/requirement census, complete fixture/oracle inventory and
documentary/interface qualifications remain pending. A current ledger
review does not ratify the whole PDF or turn the recommendations in
4.2 p7-p8 into mandatory processor documentation.

The initial C1514 scalar-character LEN-only negative and one-rank-change
control are compile-only, unreviewed fixtures. Their draft S7.2-003 link
clears an authoring gap, not the review gate. Updating that requirement's
pending/oracle text intentionally stales its three pre-existing direct
cases and the 7.2 catalogue review; it does not change their source inputs
or refresh approvals. The case/metadata/requirement fingerprint algorithm
and all unrelated default metadata are unchanged.

## Finite source-use inventories (non-executable prototype)

The optional `source_uses` index entry names a canonical repository-relative
JSON registry. `doc/evidence/source_uses.json` initially has no inventories:
this is infrastructure, not completion of any pending source-use facet.
An inventory connects occurrences in the pinned source to their defining
requirement or an explicit overriding production. It does not create,
select, approve, or execute a Fortran case.

Each inventory has an `id`, a structured R/C/S `target` with `requirement`,
`facet` and `source_units`, a nonempty `basis` of dependency anchors, explicit
`sections`, `claim`, `limitation`, `entries`, and `coverage_credit: "none"`.
The target facet must remain pending. The denominator is every current
base and fine source unit in those complete sections, derived from the
pinned census and catalogue subdivisions rather than from the supplied
entries. An omitted entry is reported as `missing`; an empty entries array
therefore cannot shrink the denominator. Adding or removing source units
changes the content binding. Base and fine counts remain separate.
`occurrence_record_count` counts declared records, not distinct physical
text occurrences across overlapping parent and fine source anchors.

An entry has an exact `source` anchor, `disposition` (`mapped`,
`not-applicable`, or `pending`), substantive `rationale` and `occurrences`.
Mapped entries need occurrences, not-applicable entries cannot have them,
and pending entries may retain already identified occurrences. Each
occurrence declares the exact `term`, its positive one-based `ordinal`
within that source unit, `resolution` (`target` or `explicit-override`),
`definition`, `dependencies` and `rationale`. The ordinal distinguishes
repeated occurrences of the same term, not source line numbers. A target
resolution must use a declared target anchor; an override must use another
defining anchor. All definitions and dependencies must be explicit in the
target or basis. These are authored source judgments, not parser-generated
proofs: independent review must inspect the original passages, contexts,
exceptions and omitted occurrences.

Source review binds the complete finite universe, all entries and
occurrences, target requirement, dependency source material and relevant
catalogue reviews. Missing, draft or stale prerequisite catalogues block
approval. Explicitly pending and missing entries may remain in a current,
honestly incomplete inventory. `classified_scope` concerns only its
declared finite section set, is separate from review state, and cannot
clear the target facet or ratify the whole standard. Changing that set,
an occurrence, a source subdivision or relevant source review makes the
receipt stale; historical review anchors are retained for readjudication,
not treated as a current denominator.

```sh
python3 tests/run_tests.py --record-source-use-review INVENTORY_ID \
    --review-state source-reviewed \
    --review-rationale 'Independent review of the exact source-use scope and remaining gaps.'
```

This operation needs neither selected fixtures nor a compiler. It cannot
accept reference validation or a compiler report, and writes only the
source-use registry. `--audit`, `--list` and JSON reports expose inventories,
missing/pending members and current review status without execution or
passing-effect counts. A case selector never filters the source universe.
Draft or stale inventories make the ordinary audit incomplete, but do not
veto an independently approved case run or baseline update: they supply no
executable evidence. A change during a report/baseline run nevertheless
makes the snapshot provisional and prevents updating expected failures.
The transaction snapshot separately binds the exact persisted inventory
review record, including its presence, state, rationale, sources and stored
fingerprint. A rationale-only re-review is therefore detected even when
semantic content and effective review state are unchanged, including a stale
receipt whose rendered rationale is generic. This does not put the review
record recursively into its own semantic approval fingerprint.

This prototype does not implement documentary processor qualifications,
reporting-capability configurations, graph-to-case reuse, or a complete
assumed-term census. Canonical case links and the execution ledger retain
their existing roles and fingerprints. All 29 foundational pending facets
remain pending until their actual evidence and completion gates are met.

## Expected failures and coverage

Only observed failures are recorded by `--update-xfail`. Filtered-out,
skipped, and harness-error entries are preserved rather than silently
removed. Newly generated baseline lines omit trailing whitespace; original
diagnostic notes/output and retained entries are not rewritten.
The update command still returns the pre-update verdict; run again
to check the new baseline. Review fixtures and reference disagreements
before updating it.

`PASS`, `XFAIL`, and exit code 0 describe the selected run, not full-standard
conformance. `--coverage` reports case inventory and outcomes, not complete
facet coverage. Positive controls, context-only cases, optional-profile
skips, and unexecuted multi-image cases remain distinct. Compiler/reference
observations and the remaining S facets are recorded in the catalogue.
