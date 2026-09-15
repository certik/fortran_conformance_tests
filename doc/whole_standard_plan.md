# Whole-standard rollout plan

## Decision

Proceed as a sequence of reviewed, resumable batches, not one prompt that
generates the entire standard. Keep compiler fixes separate from fixture
authoring. An LFortran XFAIL is not an obstacle to writing a valid test;
an unknown oracle or an unreviewed fixture is an obstacle to approving it.

The readiness refactoring now supplies:

* a checksum-pinned source census of 1,533 numbered sections and 6,473 base
  source units, including all 1,168 distinct R/C identifiers;
* generic structured catalogues and generated human-readable definitions;
* explicit unresolved source units and pending facets, rather than a
  hard-coded list for one subclause;
* byte-preserved fixtures, ordered Fortran/C builds, separate linking,
  external input/output oracles, and declared termination expectations;
* fixture review states tied to input/profile/requirement fingerprints,
  independently of compiler outcomes and expected failures;
* a real library-backed, two-image execution of the existing cross-image
  context case.

This is infrastructure readiness, not completed conformance coverage.
The current census still has 5,130 unresolved base units and five unresolved
fine-grained units inside the calibration catalogues. Its independent visual
review is still pending. Automatic PDF extraction is not semantic review,
and list items/table rows require additional audited subdivisions.

## 1. Sources of truth and resuming work

| Information | Persistent location |
| --- | --- |
| Pinned document identity and catalogue index | `doc/catalogues/index.json` |
| Generated PDF structural census and content hashes, without body text | `doc/source_inventory.json` |
| Authored requirements, source-unit dispositions, facets, and pending reasons | `doc/catalogues/*.json` |
| Generated readable definitions | The catalogue's declared Markdown render target |
| Ordinary test programs | `tests/clause*/` |
| Multi-file, verbatim, or externally judged fixtures | `tests/fixtures/*/fixture.json` and their declared files |
| Fixture adjudication and reference evidence | `tests/reviews.json` |
| LFortran regression status | `tests/expected_failures.txt` |
| Per-run configuration, diagnostics, hashes, and build traces | Uncommitted `--report` artifacts |

Use this session to finish/review the infrastructure checkpoint. After that
checkpoint is committed, start a fresh coordination session at that commit.
The current long conversation should not be the project's only memory, nor
should its entire history be copied into every worker.

On resume, inspect the worktree and this plan, then run:

```sh
python3 tests/run_tests.py --audit
python3 -B -m unittest discover -s tests -p 'test_*.py'
```

Use `/resume` for an existing session, `/fork` when intentionally branching
an investigation, and `/compact` only after recording the handoff in durable
files. `/context`, `/tasks`, and `/usage` help monitor the session. These
commands are documented by the installed CLI help; they are not a substitute
for repository state.

## 2. Work units and ordering

A work unit owns one semantically coherent subclause, or a small group of
short related subclauses. Do not assign all of Clause 16 or all of Clause 19
to one context window. A dense section may need a requirements pass followed
by several small case-authoring batches.

| Wave | Source areas | Reason |
| --- | --- | --- |
| 0 | Source census, 4.1/4.2, and shared definitions from 3, 5, and 19 | Establish classification, diagnostic obligations, and dependencies |
| 1 | 6; straightforward portions of 7 and 8 | Exercise lexical/raw sources and elementary declarations |
| 2 | Remaining 7-10 | Types, allocation, association, expressions, and assignment |
| 3 | Ordinary control flow in 11; 12 and 13 | Execution, I/O, external fixtures, formatting, and termination |
| 4 | 14 and 15 | Modules, submodules, separate compilation, interfaces, and procedure semantics |
| 5 | 16, grouped by intrinsic families | Use a template for argument/rank/kind/result obligations without conflating them |
| 6 | 17 and remaining processor-dependent profiles | IEEE state and independently justified numerical oracles |
| 7 | Remaining coarray/image work in 11/16; 18 | Multi-image behavior, C descriptors, and companion-processor interfaces |
| 8 | Remaining 19, cross-clause interactions, and informative material | Close source-accounting gaps and audit dependencies |

This is a scheduling preference, not an excuse to omit later dependencies.
For example, variable-definition contexts from Clause 19 must be read when
authoring earlier constraints that reference them. Audit informative
annexes and notes for their role and cross-references; do not turn them into
new mandatory requirements merely to create tests.

## 3. Per-work-unit protocol

1. **Inventory before implementation.** Select every source unit in scope
   from the pinned census. Read the original PDF, not just an existing
   summary. Subdivide lists/tables and classify each item as an R/C/S
   mapping, definition, permission, informative material, or unresolved.
2. **Extract requirements.** Reuse official R/C IDs and allocate append-only
   S IDs within the defining subclause. Record the full conditions,
   exceptions, diagnostic obligation, and a finite facet plan. New facets
   without tests must be explicitly pending with reasons.
3. **Review the inventory independently.** A reviewer starts from the
   source and asks what was omitted or overstated. Fix the catalogue
   before producing a large batch of programs.
4. **Author small fixtures.** Use independent cases where feature support
   would otherwise mask other results. Specify exact observable outcomes;
   use minimally repaired conforming controls for negative cases.
5. **Collect observations.** Run the selected cases with reference
   compilers and LFortran using versioned toolchains. Draft runs use
   `--allow-unreviewed`; their compiler results do not approve the fixture.
6. **Adjudicate.** Record either fingerprint-matched reference validation
   or a specific source-only rationale. Disputed cases and missing oracles
   remain blocked. Reference disagreement is evidence to investigate,
   not an instruction to change a correct oracle until it passes.
7. **Integrate serially.** The integrator checks the complete catalogue,
   generated views, fixtures, and regression tests, records approved
   reviews, and only then updates LFortran's expected failures.

Finish with a reviewed commit or PR for that work unit. Keep a compiler
bugfix out of that change unless explicitly requested as a separate stream.

## 4. Subagents and file ownership

Start with **two authors and one independent reviewer at most**, plus a
coordinator. This is a proposed concurrency budget, not an approved factory
run or a reason to spawn agents now.

| Role | Bounded responsibility | Must not do |
| --- | --- | --- |
| Coordinator/integrator | Allocate scopes/IDs, resolve questions, merge, approve reviews, update baselines | Treat a green baseline as proof of source completeness |
| Requirements author | Catalogue one assigned source scope, including omissions and dependencies | Infer obligations from compiler behavior alone |
| Case author | Implement a small approved requirement set and collect results | Approve its own cases or hide failures by updating xfails |
| Independent reviewer | Audit source accounting, premise validity, oracles, and evidence | Review only the author's summary or demand a trap for undefined behavior |
| Test executor | Run bounded commands and produce compact reports | Make semantic decisions or quietly omit failed/skipped configurations |

Use separate git worktrees for concurrent authors. A worktree can contain
the local index changes needed to test its work, but the integrator owns
the shared index merge, `reviews.json`, and the regression baseline.
Do not run several agents that edit the same checkout or the same
subclause/ID namespace.

Each worker packet should contain only:

* the task's source IDs, PDF identity/hash, and relevant page ranges;
* the complete normative passages and necessary referenced definitions,
  accessed from the original PDF;
* the relevant catalogue JSON, representative existing cases, and current
  reference observations;
* the exact owned paths, required outputs, acceptance checks, and stop point.

Do not send the whole PDF or every run log to every worker. Do not launch
overlapping investigations "just in case." A reviewer should receive the
source and acceptance criteria in a fresh context before reading the
author's conclusions.

For a future large factory, first approve its scope and explicit credit,
concurrency, and total-agent limits. Use a durable work queue and resume
completed stages instead of restarting the whole book. No factory has been
created or started by this refactoring.

## 5. Initial model choices

These are starting recommendations, not measured Fortran benchmark
rankings. Model availability depends on the account and CLI configuration.
Use the current `/model` picker and `/subagents` settings before scheduling;
this change does not modify those settings.

| Role | Initial choice | Policy |
| --- | --- | --- |
| Coordinator and difficult normative extraction | GPT-6 Astra (`gpt-6-astra`), the model used for this session | Prefer strong reasoning over throughput |
| Routine fixture implementation from approved requirements | Claude Sonnet 5 (`claude-sonnet-5`), or the coordinator model for difficult cases | Evaluate on the calibration packet before scaling |
| Independent semantic review | Claude Opus 5 (`claude-opus-5`) in a fresh context | A different model/context can expose correlated mistakes; it is not proof of correctness |
| Deterministic scaffolding/report formatting | Scripts first; optionally Claude Haiku 4.5 (`claude-haiku-4.5`) | No authority to invent requirements, approve fixtures, or change oracles |

GPT-5.4 (`gpt-5.4`) is also a concrete alternative for implementation/review
if that better matches available access or the measured pilot results.
Do not assume a less expensive or faster model has sufficient standards
expertise merely because its output compiles.

Before the first broad wave, compare candidate models on the same bounded
packet: source-form continuation/EOF, scalar-RHS allocation, finalization,
format-diagnostic exemptions, undefined opaque values, and the C/termination
calibrations. Score omitted requirements, invalid "valid" cases, unjustified
oracles, and review escapes, then measure elapsed time and actual usage.
An accepted result must have no known fixture-validity defect. Increase
parallelism only after the reviewer can keep up with the authors.

The installed CLI help confirms `/model`, `/subagents`, `/fleet`, `/tasks`,
`/resume`, `/fork`, `/compact`, `/context`, and `/usage`. Model names above
were checked against GitHub's supported-model documentation:
`https://docs.github.com/en/copilot/reference/ai-models/supported-models`.
Custom-agent workflow guidance:
`https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents`.

## 6. Acceptance gates

| Gate | Required condition |
| --- | --- |
| Structural | Known source IDs; every scoped base/fine unit classified; no duplicate IDs or unknown facets |
| Source | Complete premises/exceptions and diagnostic obligations; independent review of the source census |
| Fixture | Complete declared inputs/builds, meaningful oracles, correct evidence class, and explicit profiles |
| Reference | Successful observations or a specific source-only adjudication; never pretend unsupported modes validate a case |
| Approval | Current input/profile/requirement fingerprint matches the adjudication record |
| Regression | No unexplained failures, XPASSes, harness errors, or skips in a required calibration configuration |
| Final source closure | `--audit --require-complete-source` succeeds after the census is independently ratified |

Use exact per-case evidence rather than a single percentage. Keep source
accounting, authored facets, actual executions, passing effects, positive
controls, context-only cases, and profile limitations separate.

A changed fixture invalidates its approval. A new compiler failure does
not automatically invalidate an unchanged, well-founded fixture. Compiler
versions and frozen installation prefixes should be fixed per batch; the
runner checks reported versions and fixture/requirement fingerprints again
before publishing a report or updating a baseline. This check cannot detect
every uncommitted compiler change that retains the same version string, so
do not test against an installation another process is actively rebuilding.

Catalogue source reviews are also content-bound. Final source closure
requires an explicit reviewed catalogue for every content-bearing section,
including sections consisting only of numbered rules. Removing a fine
subdivision or changing its disposition invalidates the catalogue review;
it cannot silently reduce the unresolved-unit count under an old approval.

## 7. Calibration results and remaining limits

The multi-file C bridge, byte-preserved fixed-form/EOF pair, and external
input/output plus `STOP 200` contract all met their declared expectations
with LFortran, GNU Fortran, and Flang. The C companion was Apple Clang 17.
The status-200 expectation is explicitly a POSIX processor profile, not
a universal Fortran exit-code requirement.

The existing cross-image fixture was also compiled against `libcaf_mpi`
and executed with exactly two images using GNU Fortran 14.4.0, MPICH 4.3.2,
and OpenCoarrays release 2.10.3 at commit
`3d0fa68dc95f05f9c17bd3e7dd0d34e6f530e429`. The runner's CAF adapter,
launcher argument substitution, and `--no-skips` path were exercised.
The source checks remote ordinary payloads and requires at least two
images; it never reads the undefined opaque results.

The same MPI-backed toolchain also ran the same-image team and
unallocated-coarray controls. The allocated-coarray component case still
failed its destination-bound oracle, as the newer single-image GNU run
did. That case remains source-reviewed only, with its source rationale
and reference disagreement recorded rather than hidden.

The two enum fixtures and the new `.NIL.` token control still have no
successful runtime reference result. Six assignment facets still need
explicit diagnostic-policy decisions or independently justified
processor-specific expectations. Four prescribed-graphics facets need a
reviewed processor source/display-interface evidence contract: accepting
characters in a program does not establish their graphic appearance.
Ten additional-character facets still need qualified source-interface or
external-record evidence. The two external UTF-8 cases can use existing
byte-preserved fixtures once their documentary premises are established.
Three fixed-source line/kind facets need qualified input mappings, and the
character-context missing-successor condition still lacks a discriminating
oracle. A generic EOF or missing-END report cannot silently close it.
Two INCLUDE facets still need an authoritative separator interpretation
or qualified numeric-selector interface. Twenty-nine foundation facets
need source/use-graph, documentary/interface, or finite aggregate evidence.
Those contracts must retain their finite coverage boundary rather than
claiming proof of every possible program.
The first type batch added 21 explicit pending facets. LEN-only generic
exclusion now has a reviewed finite canonical-case link, without a duplicate
execution or universal claim. Six PDT mechanism facets now have seven
independently reviewed effect programs, all executed by GNU. Target and
Flang feature failures remain explicit, as do untested zero-LEN transitions
and the five remaining 7.2 source/use-graph facets. The following compatibility
batch adds five source-use/identity gaps. Other source/use-graph and C710
isolation questions remain separate.
The integer batch adds four source-use, inventory and processor-value-set
gaps. Its binary-model branches and identifier bounds are qualified
witnesses, not universal representation assumptions.
C descriptor header discovery is now calibrated, but broader descriptor
interfaces and the remaining IEEE/profile families still need their own
work units; the basic C bridge does not cover them.

## 8. Rollout progress and next batch

`doc/rollout_progress.json` records reviewed batch checkpoints. The first
nine implementation batches catalogue the content-bearing sections of
Clause 6, 4.1.1-4.1.5/4.2, 7.1-7.3, and the intrinsic/integer sections
7.4.1/7.4.2/7.4.3.1, using
separate author worktrees and review independent of those authors.
All except the third batch used fresh review contexts. The third review task
returned no substantive result, so the coordinator performed that source
and fixture review directly; it is not reported as a fresh-context review.
The coordinator
continued in the existing session, while authors and reviewers received
fresh bounded contexts. No large factory or per-agent model override was
used, so this is not an A/B model benchmark.

The preliminary census audit verified global bookkeeping and sampled
twelve PDF pages. It did not ratify the whole census. It exposed a
numbered-only closure loophole and missing content binding for catalogue
reviews; both now have regression coverage. The subsequent fixture review
also found and repaired a short-diagnostic-format omission in manifest
rejection tests. See `doc/source_audits/`.

The second checkpoint adds Constants and Operators: eight structured
numbered requirements, 38 facets, and 45 executions. Review exposed a
DATA-repeat diagnostic fallback; count-neutral named cases now distinguish
missing integer-type rejection from an unrelated object/value-count error.
Restated operator syntax remains owned by its defining Clause 10 subclause.

The third checkpoint adds seven requirements and 27 executions, separating
five effect programs from 22 admission controls. A direct character-equality
oracle replaces an unnecessary default-integer character-code premise.
Digit definitions receive source accounting without a synthetic effect
test, and the `.NIL.` fixture retains source-only approval rather than
invented reference corroboration. The four new graphics facets remain
explicitly pending.

The fourth checkpoint adds eight requirements and 81 executions, including
all 32 special-character table members, all 28 optional keyword-spacing
entries, and exact 10000/10001-character line boundaries. Its opt-in
`diagnose` fixture contract distinguishes relevant nonfatal reporting from
fatal rejection. Nine migrated cases preserve their original source bytes
and execution IDs; all pre-existing fixture fingerprints are unchanged.
The END TEAM control is explicitly compile-only. Three unanimously
accepted negatives retain source-only approval rather than altered oracles.

The fifth checkpoint adds 23 requirements and 87 executions while preserving
and readjudicating the original CRLF calibration. Both source forms have
independently reconstructed million-character boundary pairs. Explicit
statement spans and one narrowly input-bound GNU driver warning repair
three attribution mismatches without accepting unrelated reports.
A new one-edit missing-successor EOF pair is diagnosed by LFortran and
Flang; GNU's compiler crash remains a failed observation. The separate
character-continuation EOF facet is not conflated with that result.

The sixth checkpoint adds 26 requirements and 67 executions. All Clause 6
source units are now classified and reviewed, with explicit oracle gaps.
Declared included-file diagnostics no longer depend on filename suffixes;
two GNU cycle reports are recognized without accepting crashes or generic
depth limits. A `recommendation` disposition closes eight advisory
accounting entries without claiming mandatory or implemented documentation.
The foundation's 29 aggregate/documentary/source-use facets remain pending.

The seventh checkpoint adds 27 type requirements and 132 type cases.
Fifty-two remain source-reviewed only, including every declaration
reflection effect probe; unsupported parsing is not executed evidence.
It also qualifies the eight legacy argument-kind IDs and adds their eight
compile-only repairs. Two target character-profile branches remain
explicitly unavailable, not passing or failed association executions.
Exact-point and semantic-message gates were tightened, with C1401's
genuine PROGRAM/END relation expressed by explicit spans and minimal
controls. Two older nonmatching-range passes are now gate misses.

The eighth checkpoint adds 14 requirements and 72 executions, plus one
independently adjudicated finite link from the C1514 pair to the LEN-only
generic exclusion. Direct authored, linked, and observed/passing evidence
remain separate. Per-processor C binding headers are staged without
shadowing the C companion's standard headers, and optional mapping premises
are probed before the descriptor fixture.

The target changed externally to a dirty 411 build during that batch.
Its binary/runtime/module/header set is now frozen in session artifacts;
all 619 prior outcomes were unchanged on those frozen bits. The advertised
header and produced descriptor versions still disagree, so that failure
is recorded as an interface mismatch before local propagation is observed.
Frozen copies and successful linking are not ABI certification.

The ninth checkpoint adds 21 requirements and 93 executions, including
seven true PDT effects. Independent review exposed an unguaranteed
conversion of a processor KIND identifier and noncausal diagnostic
predicates in all twenty new negatives. The identifier conversion now has
a separate sufficient profile, while positional/keyword and mandatory
integer-capacity controls remain unconditional. Case-specific diagnostic
gates remove four target and four reference credits without changing the
negative/control sources. Eight existing source-unchanged effects and the
whole-7.2 canonical-link binding were readjudicated.

The complete frozen-target checkpoint has 784 executions: 532 PASS,
248 XFAIL and four explicit optional-profile SKIPs. All 691 prior outcomes
are unchanged. This is a regression checkpoint, not whole-standard closure.

The subsequent observational-ledger review corrected two older BOZ
adjudications. GNU's f2023 compilation failures and Flang's f2018 successes
do not constitute qualifying f2023 reference validation. The integer
effect has a source-supported oracle and is now source-reviewed. The real
effect's numerical/IEEE model probe does not establish its internal
bit-sequence interpretation, so that unchanged case is explicitly
**needs-oracle** until an independent representation/ordering premise is
available.

The current normal run therefore reports 531 PASS, 248 XFAIL, four SKIPs
and one NEEDS_ORACLE and intentionally returns nonzero; normal audit also
refuses that unapproved oracle. Raw target outcomes are unchanged. Do not
turn the needs-oracle state into an XFAIL or regard its passing output as
approval. Observation mode remains available, but is not a completion gate.

The ledger has a separately reviewed exact inventory. Current explicit
unresolved adjudications can remain in that inventory without receiving
qualified passes, baseline updates or completed-facet credit. This permits
unrelated individually approved work to proceed while preserving the
entire denominator. Exact ordered commands, input/profile hashes, source
root/private context, compiler modes, launcher/companion/header provenance
and actual stdin are checked. Independently reviewed defects in those
relationships and a timeout-drain hang were repaired. Per-case sidecars
now support the forthcoming C722/C726 migrations without deleting their
original source files or assigning a union of facets to every case.
See `doc/source_audits/execution_ledger_001.json`.

The next units are real/complex/logical types and literals in
7.4.3.2/7.4.3.3/7.4.5, and the character subclauses 7.4.4.1-7.4.4.4.
Their seven source plans have been independently reviewed before fixture
generation; both isolated authors are implementing the bounded plans and
the explicitly required legacy migrations.
The broader meta-evidence contract, including mixed FORMAT
diagnostic contexts, is not complete merely because one link type exists.
Meta-level definitions must not become fabricated passing programs.
Continue to separate reporting, selected interfaces, finite controls, and
universal claims; all remaining source and evidence gaps stay explicit.
