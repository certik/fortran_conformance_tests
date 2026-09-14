# Fortran 2023 conformance test suite: design and plan

Status: working standalone suite under `tests/`, with generic catalogue
and fixture infrastructure. LFortran-tree CMake integration and the
compiler-side diagnostic catalogue remain planned. The rollout strategy
is in `doc/whole_standard_plan.md`.

## 1. Goal

Trace the pinned Fortran 2023 source to reviewed requirements and finite
evidence: the 502 syntax rules and 666 constraints in
`doc/fortran_2023_rules.txt`, normative prose, qualifications, and separately
classified definitions, permissions, recommendations and informative text.

For testable facets, use conforming execution assertions, small admission
controls, or isolated nonconforming inputs with source-justified reporting
oracles and minimal repairs. An assumed syntax alias or meta-language
definition does not need an artificial invalid twin. A finite control does
not prove every possible program's behavior, and source accounting does
not substitute for execution or documentary evidence.

Drive LFortran under the declared standard mode, source form and processor
profiles. Keep required reporting distinct from stronger rejection and
rule-code policies. Reviewed implementation gaps may remain XFAILs; they
do not approve a fixture or establish full-standard conformance. Coverage,
fixture validity, actual observations and passing effects are separate.

## 2. What the standard itself says about detectability

F2023 4.1.2 distinguishes constraints from broader textual restrictions.
Section 4.2 requires detection/reporting capabilities for syntax and
constraint violations, with the explicit paragraph-3 exception for format
specifications outside FORMAT statements. It also names obligations outside
the numbered inventory, including source-form and scope/name checks.
Error severity, rejection, and a particular rule code are additional
LFortran test-contract choices, not interchangeable with the standard's
general detection/reporting requirement.

Consequences:

1. **Classify the diagnostic obligation, not merely the ID prefix.**
   Numbered diagnostic cases are normally compile-time checks, but the
   C1302 character-format cases are explicitly an additional diagnostic
   policy, not mandatory detection under 4.2.
2. **A missing implementation does not waive a required obligation.**
   Keep required behavior distinct from optional processor facilities,
   processor profiles, and extra diagnostic policies.
3. **Conforming execution tests need to run**, under LFortran and under
   reference compilers where supported. Reference agreement corroborates
   source review; it does not prove validity or replace the standard.
   Section 5.1 shows why both review and execution matter.

### 2.1 What is *not* an R/C rule

Requirements also appear in prose, definitions, lists, and tables outside
the numbered R/C items. These include program restrictions, specified
execution effects, and qualifications on processor choices. They cannot
all be represented by a compile-time rejection test, nor found by
extracting only sentences containing "shall".

The first executable `S` prototype selected mixed-kind argument mistakes.
Its legacy file `clause15/S15_5_2_4_invalid.f90` and markers such as
`! {error S15.5.2.4 real4-to-real8}` remain unchanged for compatibility
with the current runner and xfail list. In the pinned J3/24-007 source,
however, ordinary dummy argument type compatibility is in 15.5.2.5
paragraph 2 and kind agreement is in paragraph 3.

A systematic requirements catalogue is now prototyped in
`doc/fortran_2023_S10_2_1_3.md` for intrinsic assignment. It gives each
supplementary requirement a suite-owned identity such as
`F2023:S10.2.1.3-001`, a summary, exact source anchors, named facets,
and proposed test oracles. Source accounting is separate from executable
coverage and compiler results. The source document, not the summary,
remains authoritative.

The first executable batch has 41 programs for all 32 catalogue IDs, with
named facets and evidence classifications in their headers. The runner
supports their extended IDs, independent file variants, optional processor
profiles, and coarray execution requirements. The catalogue records which
facets and reference executions remain unverified.

S requirements are not subject to a mandatory valid/invalid pair. A
specified runtime effect need not have an invalid counterpart, and a prose
restriction does not by itself mandate a diagnostic or a runtime trap.
The three restriction entries currently have positive controls; the
undefined-result entry has explicitly context-only cases. Diagnostic-policy
tests would need their obligations specified separately.

## 3. Layout

```
doc/
    catalogues/index.json         catalogue registration and document identity
    catalogues/*.json             authored definitions, facets, source accounting
    source_inventory.json         generated structural census and content hashes
tests/
    README.md
    run_tests.py                  runner and approval-aware audit
    expected_failures.txt         xfail list, regenerated by the runner
    reviews.json                  fingerprinted fixture adjudication
    fixtures/*/fixture.json       multi-file/raw/external-oracle fixtures
    clause04/ ... clause19/
        C726_valid.f90            one conforming program, all facets of C726
        C726_invalid.f90          many invalid cases, one program unit each
```

**A primary valid/invalid pair per numbered rule, with independent cases
where needed.** Modules needed by a program go into the same file before
it. Additional executable cases use `<RULE>_valid__<variant>.f90`: for
example, C1401 needs separate main programs for its allowed forms, and
S10.2.1.3-008 separates ordinary character allocation from PDT support.
Each is a separate result and xfail key.

The double underscore distinguishes an independent case from an auxiliary
source. A `tests/fixtures/*/fixture.json` now explicitly lists all auxiliary
files, compile order, dependencies, link inputs, and expectations. Such
sources are never accidentally discovered as standalone tests. The original
single-file conventions remain supported.

A compile-only manifest can explicitly choose `outcome: "diagnose"` when
the oracle requires a relevant report rather than fatal rejection. Such a
fixture is still invalid input. Its source file/line or declared statement
span and constrained
nonfatal-message predicates are independent of ordinary process exit
status; crashes, timeouts and earlier build failures remain failures.
This opt-in contract does not relax the existing `reject` outcome or
ordinary isolated-negative policy. See `tests/README.md` for the schema.

The rule id is spelled as in the standard (`C726`, `C7100`, `C15121`), with
no zero padding, so file names are greppable with the string used in the
standard, in compiler messages and in `doc/fortran_2023_rules.txt`. The
directory is the clause, which the rule number already encodes. Rules that
clause 5 restates (`R1401` shown under 5.1 and 14.1) get their files under
the clause that defines them.

### 3.1 The valid file

Conforming programs, plus modules if needed, collectively exercise the
rule's facets: alternatives, list items, optional parts, supported kinds,
rank boundaries, empty lists, and syntactic contexts. Results are checked
with `if (...) error stop`; nothing is printed on success. Each executable
case must exit 0. The catalogue cases also record any processor profile or
image configuration needed before their result can be judged.

An aggregate rule result must still require all applicable cases, but one
unsupported feature should not hide independently working facets. For
example, S10.2.1.3-008's `__pdt` case can fail independently of its
character-only case. Existing combined prototypes such as C726 are not
automatically split by the runner.

### 3.2 The invalid file

```fortran
! C801 (R801) The same attr-spec shall not appear more than once in a given
! type-declaration-stmt.
subroutine c801_allocatable()
    implicit none
    real, allocatable, allocatable :: b(:)   ! {error C801 allocatable}
    allocate(b(2))
end subroutine
subroutine c801_intent(x)
    implicit none
    integer, intent(in), intent(in) :: x   ! {error C801 intent}
end subroutine
module c801_public
    implicit none
    integer, public, public :: m = 1   ! {error C801 access-spec}
end module
```

* **Each case is compiled independently.** New files use `! case: <case-id>`
  boundaries around complete fixtures, which can include several supporting
  units. Multiple main-program cases may coexist in the container file
  because they are never submitted together.
* **Each case violates the rule exactly once**, and the offending line carries
  `! {error <RULE> <case-id>}`. The case id is a short kebab-case word that
  survives renumbering of lines (it is what the xfail list refers to).
* **Legacy free-form files use column-1 top-level `end` statements as
  boundaries.** Unmarked helper units are retained. Other cases are blanked
  out, preserving original line numbers. Fixed-form or missing-END cases
  need explicit boundaries rather than a heuristic Fortran parser.
* Everything else in the file is conforming. Cascade errors are the
  compiler's problem, not the test's, and are reported by the runner as a note
  rather than a failure (see 4.1).

**How many cases per rule.** Enumerate three things and take the product
where it makes sense:

1. the *facets* of the rule text: every list item of a constraint, every
   alternative of a syntax rule, every "or" and "unless";
2. the *syntactic contexts* in which the construct can occur: attribute in a
   type declaration vs attribute statement vs component definition vs dummy
   argument vs function result vs `entity-decl` in an interface body, a
   format in a `FORMAT` statement vs a character literal, a generic defined by
   `module procedure` vs an interface body vs a type-bound generic, and so on;
3. the *compiler paths*: when it is known that LFortran handles a construct in
   more than one place (symbol table visitor vs body visitor, declaration vs
   `intent` statement, fixed vs free form tokenizer), add a case for each.

Cases from (3) are legitimate even though the standard does not distinguish
them: the suite is for finding LFortran bugs, and "the same error from a
different path" is a different bug. When a bug is found by other means later,
its reduced reproducer is added as one more case in the rule's invalid file.
This is how the invalid files grow over time; they are never "finished".

The prototypes show that 4–6 cases per constraint is the typical size and
that (2) is where most of them come from: C815 has five cases that differ
only in which attribute statement repeats the attribute, and LFortran
detects exactly one of them.

### 3.3 Kinds

Every compiler supports a different set of kinds, so a test must not depend
on any kind beyond the guaranteed set, and must not need a preprocessor to
adapt. What the three compilers offer today (`ISO_FORTRAN_ENV` kind arrays):

| type | LFortran | gfortran 13 | flang 18 |
| --- | --- | --- | --- |
| integer | 1 2 4 8 | 1 2 4 8 16 | 1 2 4 8 16 |
| real | 4 8 16 | 4 8 10 16 | 2 3 4 8 10 16 |
| complex | 4 8 (no 16) | 4 8 10 16 | 2 3 4 8 10 16 |
| logical | 1 2 4 8 | 1 2 4 8 16 | 1 2 4 8 |
| character | 1 | 1 4 | 1 2 4 |

Rules:

1. **Tests use only the common subset by default**: integer 1, 2, 4, 8;
   real and complex 4, 8; logical 1, 2, 4, 8; character 1. It is enough:
   kind is rarely the point of a rule, and where a rule needs "two different
   kinds" or "a non-default kind", 4 and 8 do.
2. **A kind outside the subset is never named by a digit.** When a test wants
   to cover a wider kind if the processor has one, it selects it at compile
   time with a constant expression and checks at run time whether it got it:

   ```fortran
   use iso_fortran_env, only: real64, real128
   integer, parameter :: qp = merge(real128, real64, real128 > 0)
   real(qp) :: c
   ...
   if (qp == real128) then ... extra checks ... end if
   ```

   This is conforming, needs no preprocessor, and compiles and runs on all
   three compilers (`clause07/C722_valid.f90` does it). The same idiom with
   `selected_int_kind(36)` covers 128-bit integers, `selected_char_kind('ISO_10646')`
   covers UCS-4 characters. The test is then valid on every processor, and
   exercises the wide kind wherever it exists.
3. **A nonexistent kind is always 7.** Rules C720, C722, C732, C733 ("the
   kind-param shall specify a representation method that exists on the
   processor") and the corresponding kind-selector rules need a kind no
   compiler has. It is not 3 (flang has real kind 3, bfloat16) and not 16;
   7 is free for every type on every compiler, and this is the one place
   where a digit outside the subset appears (`clause07/C722_invalid.f90`).
4. **No preprocessor, no per-compiler files.** `.F90` files would take the
   tests outside the standard, complicate the reference-compiler runs, and
   hide from LFortran exactly the code we want it to see. Per-kind file
   variants would multiply files for no coverage gain. Neither is needed
   given rule 2.
5. **No compiler options that change default kinds** (`-fdefault-real-8`
   and friends) ever; the suite runs with `--std=f23` only, and default kinds
   are what the rule text means by "default".

**Mixed-kind mistakes.** Passing `real(4)` where `real(8)` is expected,
comparing or assigning across kinds, `1.0` where `1.0d0` was meant: these
are the most common kind-related errors in real code, but almost none of
them are `R`/`C` rules. Argument type/kind agreement is normative text in
15.5.2.4 (not a constraint); mixed-kind assignment and arithmetic are
*conforming* (implicit conversion). So mixed-kind tests appear in the suite
as `S` tests where the standard forbids the mix (2.1), and as valid tests
where it allows it (the valid file for the intrinsic assignment and
numeric-operation rules must exercise every kind pairing in the subset,
with the result kind checked). The LFortran-side consequence is in 6.

### 3.4 Expected failures

`expected_failures.txt` lists failing tests one per line, keyed
`<RULE>_valid`, `<RULE>_valid__<variant>`, or `<RULE>_invalid:<case-id>`,
with the reason as a trailing comment. It is regenerated with
`run_tests.py --update-xfail`; nobody edits
it by hand. An xfail that passes is reported as `XPASS` and fails the run, so
a fix PR runs the update and commits the shrunken list. This separates the
tests (which change rarely) from LFortran's status (which changes with every
PR), as the LLVM `lit` and GCC test suites do.

### 3.5 Generic catalogue and source registries

`doc/catalogues/index.json` registers structured catalogue files. JSON
keeps the runner compatible with Python 3.9 without another runtime
dependency. Definitions, source anchors, diagnostic obligations, facets,
pending reasons, and detailed source-unit dispositions are authored there;
Markdown definition regions are generated views, not a second source
of truth. Both official R/C IDs and supplementary S IDs can have structured
facets.

`doc/source_inventory.json` is extracted from the checksum-pinned PDF.
It records all detected headings, paragraphs, numbered items, captions,
notes, and unlabelled text regions without redistributing the body text.
Known R/C items are cross-checked against the existing rules inventory.
List/table subdivisions remain reviewed catalogue data.

The generic audit checks every registered catalogue, not a hard-coded
subclause. It rejects missing source dispositions, unknown anchors,
duplicate identifiers, and mismatches between authored and declared-pending
facets. Uncatalogued source units remain explicitly unresolved.
Independent census review is still required; `--require-complete-source`
does not silently accept the current partial inventory.

Source accounting, authored cases, actual execution, successful effects,
and optional-profile limitations are distinct measurements. Definitions,
permissions, and justified non-executable material may be accounted for,
but never become passing execution tests merely to reach 100 percent.

## 4. Runner

The standalone prototype is `tests/run_tests.py`; its CLI and case-header
formats are documented in `tests/README.md`.

### 4.1 LFortran

Valid file: `lfortran --std=f23 <file> -o exe` must succeed and `exe` must
exit 0. The exceptions are explicit source-form/coarray flags and the
execution prerequisites recorded in a case's metadata, not options that
relax language rules.

Each invalid case is submitted separately using
`lfortran --std=f23 --semantics-only --error-format short <isolated-file>`.
It passes only with an unsuccessful compiler exit and a non-internal error
whose source range includes the marked line. Compiler crashes, timeouts,
and ASR-verifier failures do not count as successful diagnostics.
`--continue-compilation` is not passed: recovery is not needed to discover
the next case. Other errors are retained as notes, not substituted for the
marked diagnostic.

The `short` format is parsed rather than the human format. With `--codes`,
the expected rule must be present either in a legacy `[C801]` field or in
the proposed `[E0231] (F2023 C801)` standard-reference field.

Each process has a configurable timeout, defaulting to 30 seconds.
Unavailable optional profiles and absent multi-image launchers produce
explicit skips, never passes. A profile probe's own compilation failure
is a failure rather than evidence that the profile is absent. Full
diagnostics and configuration can be saved with `--report`.

Manifest fixtures additionally use byte-preserved source inputs, separate
compile/link steps, C companion compilation, explicit stdin/arguments,
and external output/termination oracles. An expected error at a later
stage cannot be satisfied by an earlier failure. A profiled application
exit such as STOP 200 is distinct from a compiler crash. These contracts
are exercised by the readiness calibration fixtures.

Fixture approval is stored separately in `tests/reviews.json`. A changed
input, profile, or requirement makes its adjudication stale. Draft
observations use `--allow-unreviewed`; only explicit source-reviewed or
reference-validated fixtures can enter an xfail update. The latter state
requires current fingerprint-matched reference evidence, while source-only
approval needs a specific rationale. Disputed and oracle-less cases remain
unapproved.

### 4.2 Reference compilers

`--reference gfortran --reference flang` (repeatable) runs the same isolated
cases through each reference compiler. The default probes `f2023`, then
`f2018`, and reports the actual version and mode; `--reference-std` can
override the selection. F2018-mode rejection of an F2023-only construct
does not establish that a fixture is invalid.

A valid case must compile and run. An invalid case normally needs a
nonzero exit and an error within the selected case, not necessarily on
LFortran's chosen line. For specifically identified nonconformance
diagnostics, a case may also allow a reference warning code: C601 permits
Flang's `[-Wlong-names]` portability diagnostic. This is shown as
`diagnoses`, not `rejects`, and does not relax LFortran's required error
severity. Arbitrary warnings and unlocated compiler failures do not
corroborate a case.

Reference results never decide pass or fail for LFortran. They are printed
next to every case and summarised, so that the authoring rule can be applied:

| gfortran | flang | meaning |
| --- | --- | --- |
| agree with the test | agree with the test | likely correct; commit |
| one agrees | one disagrees | re-read the rule; either the test is wrong or one compiler has a gap. Record the discrepancy in the header or catalogue snapshot |
| disagree | disagree | probably the test is wrong; if source review still supports it, record the rationale and the lack of reference validation explicitly |

In the original 40-case snapshot, both references agreed with the test on
29. The 11
disagreements are all reference-compiler gaps: flang 18 misses four of the
five duplicate-attribute cases of C801 and two of C815, a mixed
function/subroutine generic (C1514) and two format-comma cases (C1302);
gfortran 13 misses the repeated-slash format case and rejects the
`R1123_valid` file because it has no DO CONCURRENT locality specs at all.
The disagreements are worth recording per case (a `! references:` line in
the header, or the manifest) because they are exactly the cases a reviewer
must look at. The later intrinsic-assignment snapshot, including its
unvalidated and multi-image cases, is recorded in
`doc/fortran_2023_S10_2_1_3.md`, section 8.

### 4.3 Integration with the existing suites and CI

Valid files are end-to-end programs and belong in the integration-test
matrix (all backends, `--fast`, separate compilation). Rather than 1 000+
hand-written `RUN(...)` lines, the plan is a `conformance_tests/CMakeLists.txt`
generated from the files on disk (`run_tests.py --emit-cmake`) and included
from `integration_tests/`, so that `ctest -L llvm` covers them too. Invalid
files do not use `tests/tests.toml` and reference outputs: the pass criterion
is a rule code on a line, not the rendering of a message, so wording can
change without touching a thousand reference files. CI runs
`run_tests.py --reference gfortran --reference flang-new-18 --codes` once
and fails on `FAIL` and on `XPASS`.

## 5. Findings from the initial prototypes

Nine rules, 17 files, 46 invalid cases and 8 valid programs, chosen to be
awkward: a constraint with a five-item list of permitted contexts (C726),
generic distinguishability (C1514), an exception list on format syntax
(C1302), two near-duplicate attribute constraints (C801 vs C815), a syntax
rule with three alternatives (R1123), a plain type constraint (C1121), a
kind-existence constraint (C722) and the mixed-kind argument requirement
(S15.5.2.4). The original LFortran snapshot had 20 pass and 34 fail. In detail:

| rule | LFortran in the original snapshot |
| --- | --- |
| C726 | valid file fails (no PDT LEN parameters); 3 of 6 cases detected, two of those by the ASR verifier with an internal message, one as a *syntax* error because `allocate(character(*) :: s)` does not parse; module- and internal-function assumed-length results not detected |
| C801 | 1 of 5 detected (`dimension` twice); `allocatable`, `intent`, `parameter`, `public` twice all accepted |
| C815 | 1 of 5 detected; the valid file hits an `LCOMPILERS_ASSERT` in `asr_expr_type_visitor.h` (a crash on a conforming program) |
| C1121 | 2 of 4 detected; a real do-variable is a warning, a logical one is accepted |
| C1302 | 0 of 4: all four are warnings, and the warning text already cites "F2023 constraint C1302" |
| C1514 | 0 of 5: no generic distinguishability check exists, not even for a generic mixing a subroutine and a function |
| R1123 | 4 of 4 detected as syntax errors (message quotes the marker comment as the unexpected token); the valid file compiles but `local_init(u)` modifies the outer `u`, so it fails at run time |
| C722 | 5 of 5 detected, valid file runs; gfortran and flang agree on all six |
| S15.5.2.4 | 0 of 8 under `--std=f23` (see 6); 8 of 8 in default mode |

Nine rules found four missing checks, three checks at the wrong severity,
two checks in the wrong compiler stage, one parser gap, one assertion
failure, one code-generation bug and one option set that hides the most
common user error. The full suite will find hundreds.

### 5.1 Authoring lessons

Every one of these mistakes was made while writing 14 files, and every one
was caught by a reference compiler:

1. A "valid" test violating a different rule: `do concurrent (i = 1:3)
   local(i)` violates C1127; `do v(1) = 1, 2` and `do s%k = 1, 2` are not
   do-variables at all, because R1124 restricts them to a *name*.
2. A "valid" test with a runtime bug: `write(buf, '(I2/I2)')` into a scalar
   internal file hits end-of-record. Valid tests must be *run*, not just
   compiled, by the references.
3. An invalid case violating two rules: `character(*)` as a component
   violates C726, but gfortran reports it via the "component length must be
   constant" rule. Pick the example so the intended rule is the most specific
   violation, and say in the header which other rules arguably apply.
4. A rule mis-numbered in the header (C1120 for C1121). File name, header and
   marker must agree; a review step (or the runner) checks it.
5. Reference compilers have gaps (4.2), and they differ from each other, so
   two references are the minimum and the header must record disagreements.
6. The error location is a judgement call per rule family (which line for a
   conflict between two declarations?). LFortran's choice has to be fixed
   before mass authoring, otherwise the markers churn later.

### 5.2 Special families of rules

* **Clause 6 (source form)**: fixed-form rules need `.f` files and
  `--fixed-form`; free-form rules are lexer tests (continuation, `;`, 132
  columns, character context). The runner accepts `.f` already.
* **Clause 5 and R501–R516**: program-unit ordering; overlaps with parser
  recovery.
* **Multi-file rules**: submodules, `INCLUDE`, `bind(c)` with C (3).
* **Coarrays**: valid files need `--coarray` and possibly several images; the
  header carries an options line (`! options: --coarray`), which is the only
  exception to "nothing but `--std=f23` on the command line".
* **I/O (12, 13)**: internal files or a scratch unit; nothing persists.
* **Obsolescent features** (`ENTRY`, alternate return, `COMMON`, arithmetic
  IF) are still in the standard and get tests; LFortran must accept them
  under `--std=f23`, with its style warning.

## 6. `--std=f23` must be strictly conforming

Rule: `lfortran --std=f23` supports conforming programs and reports mandatory
syntax/constraint violations as errors under the suite's strict-mode
contract. Additional diagnostic policies are explicitly identified; this
is not a decision procedure for every nonconforming runtime behavior. Extra
options (`--implicit-argument-casting`, `--logical-casting`, ...) may relax
individual rules on top of it; the default `lf` mode remains neither a
subset nor a superset and may keep downgrading some violations to warnings.
The suite passes nothing but `--std=f23` (plus the output-format options,
which do not affect the language).

The current `--std=f23` is not that mode yet. It enables implicit typing and
implicit interfaces (both conforming), but it also enables
`implicit_argument_casting`, which is not. With `--std=f23` alone, all eight
mixed-kind argument cases of `clause15/S15_5_2_4_invalid.f90` (`real(4)` to
`real(8)`, `integer(4)` to `integer(8)`, `logical(1)` to `logical(4)`,
`character(kind=4)` to `character(kind=1)`, through internal and module
procedures) compile silently; the default `lf` mode and
`--std=f23 --disable-implicit-argument-casting` both report every one of
them as "Type mismatch in argument". So today `--std=f23` is *less* strict
than the default mode on the most common user error. The same holds for the
C1121 and C1302 warnings. Auditing the option set behind `--std=f23` is the
first LFortran-side task; the suite then finds the rest.

## 7. Error catalogue: LFortran's own codes, optional standard codes

Standard rule numbers cannot be LFortran's diagnostic identifiers: they
are renumbered with every revision of the standard (a constraint keeps
its number only by accident between F2008, F2018 and F2023), LFortran reports errors that have no rule (missing features,
extensions, internal limits) and rejects some conforming programs on
purpose in `lf` mode. So:

* **Every diagnostic has an LFortran code**, a stable identifier that is
  never reused: `E0001`, `E0002`, ... for errors and warnings alike (the
  severity is not part of the code, because the same diagnostic is an error
  in `--std=f23` and may be a warning in `lf`).
* **A diagnostic may carry standard references**: zero or more rule ids per
  standard revision, e.g. `f2023 = ["C801"]`. A code can map to several
  rules (one check for C801 and C815 is plausible) and a rule can map to
  several codes (C726 will have a code per context, because they are
  different checks in different places).
* **Rendering**: `semantic error [E0231] (F2023 C801): the ALLOCATABLE
  attribute appears twice`, in both the human and the `short` format. The
  test suite matches on the standard reference, not on the LFortran code, so
  the tests know nothing about LFortran's numbering.

**Single source of truth.** The registry is a data file checked into the
source tree, one entry per code:

```toml
[E0231]
name = "duplicate_attr_spec"
summary = "an attribute appears more than once in one type declaration"
f2023 = ["C801"]
since = "0.61"
```

A generator turns it into (a) a C++ header with an enum and a lookup table
that the diagnostic constructors take (`diag.error(ErrorCode::E0231, ...)`,
so a typo in a code is a compile error and every emission site names its
code), and (b) the documentation page listing all codes with their summary,
standard references and, when the suite exists, links to the tests that
exercise them. A CI check greps the sources for codes that are declared but
never emitted. This is the Rust `error[E0308]` model; clang's
`DiagnosticSemaKinds.td` is the same idea with names instead of numbers.

Why not extract the catalogue from the C++ sources directly: today there are
about 1 200 emission sites with a literal message (about 900 distinct
strings) and another 1 000 whose message is assembled at run time, spread
over `lfortran/semantics` (760 literal sites), `libasr/codegen` (350),
`libasr/pass` (51) and the parser (37). A scanner cannot recover a stable
identity from that, and `libasr` must not know Fortran rule numbers, which
is fine: the registry maps codes to rules, `libasr` only names codes.

Migration is incremental: the code field of `diag::Diagnostic` already
exists and renders correctly (verified with a local one-line change tagging
"Dimensions specified twice" as `C801`: the `short` output becomes
`C801_invalid.f90:10-10:5-44: semantic error [C801]: Dimensions specified
twice` and the runner's `--codes` mode accepts it). Every fix PR driven by
the suite adds the code for the diagnostic it touches; untouched
diagnostics get codes in bulk later, one clause at a time.

## 8. How the tests get written

1. One subclause at a time (e.g. 7.5.2 "Derived-type definition": R726–R731,
   C733–C745); `doc/fortran_2023_rules.txt` is grouped this way. The author's
   packet is the rules, the normative text of the subclause (extractable from
   the PDF with the same pipeline that produced the rules file), and existing
   tests for those rules.
2. For each rule, the valid file covering every facet, and the invalid file
   with the cases enumerated as in 3.2.
3. Collect draft observations with the selected reference compilers,
   `--allow-unreviewed`, and `--report`. Apply the source/review policy in
   4.2; compiler disagreement alone does not decide the oracle.
4. Record explicit fixture adjudication, regenerate catalogue views, and
   run the generic audit. Only then use `--update-xfail`.
5. One PR per subclause (10–40 files), reviewed for: file name, header and
   markers agree; one violation per case; reference results and every
   disagreement explained in the PR; no LFortran-specific behaviour relied
   on.

Fixing LFortran is a separate stream: one PR per check, flipping a set of
xfails, adding the registry entry and code for the diagnostic it introduces.
Reviewing generated tests is the bottleneck; the two-reference protocol
removes the largest class of mistakes mechanically, and the remaining review
question is whether each invalid case isolates the rule it claims to.

## 9. Open questions

1. `conformance_tests/` next to `integration_tests/`, or under it?
2. Case ids: kebab-case words as now (`allocate-dummy-deferred`), or the
   program-unit name (`c726_allocate_dummy_deferred`, longer but unique by
   construction)?
3. Which additional compiler/profile combinations should supply independent
   reference evidence? Per-fixture evidence now lives in `reviews.json`,
   with detailed observations in run artifacts.
4. Error-location conventions per rule family (5.1 item 6) need deciding
   before mass authoring.
5. Registry granularity: one code per check site, or one per "kind of
   mistake" shared by several sites? (Proposal: per kind of mistake, with a
   site-specific message; the code is what users search for.)
6. Should `run_tests.py` also drive future runtime-failure `S` tests, or is
   that a job for `integration_tests/` with `FAIL`?
7. Which `S` subclauses should follow the intrinsic-assignment catalogue
   in 2.1? Proposed next: ordinary dummy argument restrictions (15.5.2.5)
   and intrinsic argument requirements (16.9).
8. Kind subset: is dropping `real(16)`/`complex(16)` from the default subset
   right, given LFortran has `real(16)` but no `complex(16)`? (Proposed: yes;
   the `merge(real128, ...)` idiom covers it where it matters.)
