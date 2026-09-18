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
The current census still has 4,772 unresolved base units and six unresolved
fine-grained units inside the catalogues. Its independent visual
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
ten implementation batches catalogue the content-bearing sections of
Clause 6, 4.1.1-4.1.5/4.2, and 7.1-7.4, using
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

The ledger checkpoint's normal run therefore reported 531 PASS, 248 XFAIL,
four SKIPs and one NEEDS_ORACLE and intentionally returned nonzero; normal audit also
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

The tenth checkpoint adds the real/complex/logical and character subclauses:
61 requirements, 211 directly authored facets and 224 new executions.
Independent source-plan review preceded case generation. The retained
C722/C726 source paths, runtime bodies and thirteen execution IDs now have
explicit legacy qualifications and per-execution metadata rather than
coarse container claims.

Fixture review corrected two C731 wrong-subject contracts, removed six
unconstrained complex-literal punctuation routes, and withdrew one new C727
negative whose unused-external-declaration prohibition was not established.
Its interpretation facet stays pending; its two source-valid declaration
controls are admission evidence only. Twenty-four other negatives retain
specific source-only adjudications, without invented reference support.
Seven old target passes were correctly lost under stricter causal gates.

The tenth checkpoint's 1,008-case normal run reports 689 PASS, 314 XFAIL, four SKIPs
and the same one NEEDS_ORACLE. Raw target outcomes are 690 pass, 314 fail
and four skip; the unresolved oracle's passing output remains unapproved.
The normal gate remains deliberately nonzero for that case. Source
accounting, fixture approval and compiler implementation status are not
interchangeable completion measures.

The eleventh batch covers 7.5.1, 7.5.2.1-7.5.2.4 and 7.5.3.1-7.5.3.2:
35 requirements, 140 directly authored facets and 231 new executions.
Independent fixture review supports 200 reference-validated and 31
source-reviewed cases, including compiler-failing default-conversion and
dependent-default effects. The definition source-plan gate used a recorded
coordinator fallback after an acknowledgement-only delegated response; it
is not represented as a successful fresh-context source review.

Diagnostic review exposed malformed-header attribution, source/message
classification and quoted-coordinate selection defects. The corrected
checker requires classification and extraction to use the same first
unshielded coordinate and rejects candidate switching. Native-text
namespace ambiguities remain explicitly qualified rather than presented as
universally lossless parsing. The original full observation report retains
20 Flang timeouts; all 20 cases passed a separate exact-selection retry
under the unchanged 30-second budget. No failed observation was relabelled.
The source, fixture and correction receipts are in
`doc/source_audits/batch_011.json`.

The observational inventory now contains 1,239 executions, without
approving the real BOZ oracle or resolving the private-component sentence
in 7.5.2.4. The normal full frozen-target run reports 803 PASS, 431 XFAIL,
four SKIPs and one NEEDS_ORACLE; raw target outcomes are 804 pass, 431 fail
and four skip. All 1,008 prior fingerprints and target outcomes are unchanged.
The normal gate still returns nonzero only for the retained oracle block.
Twenty-three new canonical-use, inventory and interpretation
facets remain pending. Forty-three character and 41 numeric facets also
remain explicit follow-ups.

The twelfth batch covers component initialization, order and accessibility
in 7.5.4.6-7.5.4.8: 24 requirements, 113 directly authored facets and
156 new executions. Independent review supports 145 reference-validated
and eleven source-reviewed cases. It corrected a shared-order cancellation
in two output tests: named-member assignments now establish values
independently of positional constructor order.

Three independently adjudicated C7107 links reuse four primary compile
cases without adding executions or manufacturing an S-level diagnostic
obligation. General source-use and classification graphs remain pending.
The source, fixture, correction and exact-binding decisions are recorded
in `doc/source_audits/batch_012.json`; source-only cases retain their
unweakened programs and explicit lack of qualifying reference evidence.
The twelfth-batch full frozen-target run reported 885 PASS, 505 XFAIL,
four SKIPs and one NEEDS_ORACLE across 1,395 executions. Raw target
outcomes are 886 pass, 505 fail and four skip. All 1,239 prior case
fingerprints and target outcomes are unchanged; the one existing oracle
block still makes the normal whole-suite gate nonzero.

The infrastructure commits preceding type-bound integration close review and reuse
gaps without adding coverage. Native compiler `error: Internal:` reports
now override otherwise accepted warnings, without treating filenames,
source echoes or application output as compiler failures. Explicit finite
canonical-case patterns support S-owned diagnostic/control pairs and
single runtime-effect or positive-control witnesses. Their direct owners,
source anchors, phases, evidence roles and independent review gates remain
binding; links still create neither executions nor derived passing effects.
All 1,395 existing fingerprints, target outcomes/phases, four link bindings
and the observational inventory are unchanged. Four actual type-bound
connections over six existing cases have been structurally checked, but
remain unregistered and clear no pending facet.

The component-name reporting-duty correction is now independently reviewed
and integrated, with the source chain from 19.3.4 p5/p6 to 4.2 p2(6) recorded
in `doc/source_audits/component_scope_duty_001.json`. Three legal controls
have renewed requirement-bound fingerprints and qualifying reference
adjudications, with no Fortran or manifest changes. The dependent source,
three component links and complete observational inventory were explicitly
renewed; old receipts were not silently expanded to new source anchors.
This changes no case count or credited facet and does not impose a fatal
diagnostic policy.

The thirteenth batch integrates 7.5.5: 39 base and 145 fine units,
33 requirements, 90 directly represented facets and 151 new cases.
Independent source/fixture/correction review supports 126 reference-validated
and 25 source-reviewed cases. All 94 valid programs passed both reference
configurations; Flang f2018 is still not f2023 corroboration.

The three review findings are closed: finite role/property diagnostic
routes replace broad fragments, native internal failures override accepted
warnings, and generated review status remains truthful after adjudication.
C784's INTEGER-only interface explicitly retains its unavoidable C765
coupling; adding a typed witness there would defeat C784's antecedent.
Twenty metadata-bound cases were freshly observed; 131 unchanged current
rows retain their actual earlier report provenance.

The thirteenth-batch whole-target checkpoint has **1,546 cases**:
**982 PASS, 559 XFAIL, four SKIPs and one NEEDS_ORACLE**. All 1,395 prior
IDs, fingerprints and target outcomes/phases are unchanged. There are
66 catalogues, 334 requirements, 1,410 direct and four linked facets,
and 283 pending facets. The source, cause, oracle and exact-binding
decisions are recorded in `doc/source_audits/batch_013.json`. No new semantic
link was registered, and the C783 mixed-access question remains explicit.

The fourteenth batch integrates the reviewed 211-case component packet in
7.5.4.1-7.5.4.5: 43 base and 145 fine units, 32 requirements, 103 direct
facets and 33 pending facets. Independent correction review closed the
unsupported-wrapper guard gap across all 77 negatives and isolated the
C765 other-type binding with a non-passed defining-type witness. Exactly
99 bindings were freshly observed; 112 unchanged bindings retain their
original observations, with no old-row relabelling.

The packet has 160 reference-validated and 51 source-reviewed cases.
Six of the latter are valid programs retained despite unqualified reference
results, including the ENUM/ENUMERATION, all-assumed-LEN and TYPEOF examples.
Four corank effects preserve actual guarded GNU one-image execution;
they are not compile-only or multi-image substitutes. Full decisions and
the 633-record/905-trace provenance are in `doc/source_audits/batch_014.json`.

The fourteenth-batch measured whole-target checkpoint has **1,757 cases**:
**1,108 PASS, 644 XFAIL, four SKIPs and one NEEDS_ORACLE**.
All 1,546 prior IDs, fingerprints and target outcomes/phases are unchanged.
There are 71 catalogues, 366 requirements, 1,513 direct and four linked
facets, and 316 pending facets. The real-BOZ oracle and broader source
closure remain open; these measured counts are not whole-standard completion.

Independent review qualified the ordinary finalization plans after
FSRC-001 corrected three elemental references from 15.8 (Simple procedures)
to 15.9.1/15.9.3. The correction is preserved in `1bdbfbf` and `57ba04c`.
The fifteenth batch now integrates the FINAL declaration subset:
**64 compile-only cases**, representing **37 facets**, with **11 pending**.
Independent review supports 55 reference-validated and nine source-reviewed
cases; GNU f2023 compiled every one of the 39 valid controls/admissions.
Seventeen actual KIND-tuple/rank signature fixtures were also checked
against independent finite conflict models. These declarations do not
claim callback execution, runtime classification or termination evidence.

The fifteenth-batch measured whole-target checkpoint has **1,821 cases**:
**1,135 PASS, 681 XFAIL, four SKIPs and one NEEDS_ORACLE**.
All 1,757 prior IDs, fingerprints and target outcomes/phases are unchanged.
There are 72 catalogues, 372 requirements, 1,550 direct and four linked
facets, and 327 pending facets. The source/case/signature and exact
processor decisions are recorded in `doc/source_audits/batch_015.json`.

The sixteenth batch integrates the independently reviewed finalization
process packet: **17 runs**, comprising **16 effects and one positive
control**, with **29 mandatory-event checkpoints**. All seventeen have
qualifying GNU f2023 executions. Named setup, live-state guards, exact
multisets/multiplicities and required partial orders prevent constructor
cancellation, vacuous absence checks and invented sibling ordering.
Every actual event is a successful whole-allocatable DEALLOCATE.

The source-equivalent refresh split four FINAL lists into permitted
separate statements and improved failure logging without changing main
bodies, expected event sets or success behavior. The original and refreshed
runs remain separate. All current evidence comes from the refreshed run;
the two earlier compile failures that later reached runtime are not
retrospectively counted as executions.

The sixteenth-batch measured whole-target checkpoint has **1,838 cases**:
**1,142 PASS, 691 XFAIL, four SKIPs and one NEEDS_ORACLE**.
All 1,821 prior IDs, fingerprints and target outcomes/phases are unchanged.
There are 73 catalogues, 376 requirements, 1,567 direct and four linked
facets, and 332 pending facets. Full source/oracle/observer and provenance
decisions are recorded in `doc/source_audits/batch_016.json`.
Classification/source-use facets and conditional PURE/ERROR STOP/termination
observers remain unimplemented, not completion claims.

The seventeenth batch integrates eleven reviewed inheritance runs covering
eighteen facets, with thirty-five pending. M shares all25 ordered ancestry
inquiries, N shares parent-name/access observations and G shares generic
extension/override observations. Ten cases are reference-validated; the
private-parent/public-child homonym retains source-only approval despite
both reference rejections. Its justification follows normative identifier
scope and inherited accessibility, not the target's successful run or an
informative note alone.

Sixty separately preserved one-span runtime oracle perturbations built
successfully and failed at their expected checkpoints. They strengthen the
oracle assessment without becoming negative conformance cases or adopted
diagnostic policies. Exact source, namespace, association and provenance
decisions are in `doc/source_audits/batch_017.json`.

The seventeenth-batch measured whole-target checkpoint has **1,849 cases**:
**1,146 PASS, 698 XFAIL, four SKIPs and one NEEDS_ORACLE**.
All 1,838 prior IDs, fingerprints and target outcomes/phases are unchanged.
There are 75 catalogues, 385 requirements, 1,585 direct and four linked
facets, and 367 pending facets.

The eighteenth batch adds six ordinary overriding runs representing seven
facets and 24 independently checked literal observations. Same-name accessible
overrides, different-name additions, accessible/private homonyms and both
two-generation correspondence orders have distinct concrete oracles.
Named primitive receiver setup and complete matched interfaces avoid
constructor, undefined-value or unrelated interface assumptions.
Five cases are reference-validated. The unrelated private-binding homonym
retains source-only approval and its 7/7/9 oracle despite GNU/LFortran compile
rejection; a supplementary Flang f2018 run is not f2023 qualification.
All 50 remaining facets and the additional passed-object parameter-domain
question stay open.

The eighteenth-batch measured whole-target checkpoint has **1,855 cases**:
**1,151 PASS, 699 XFAIL, four SKIPs and one NEEDS_ORACLE**.
All 1,849 prior IDs, fingerprints and target outcomes/phases are unchanged.
There are 76 catalogues, 396 requirements, 1,592 direct and four linked facets,
and 417 pending facets. The newly imported explicit additional-parameter
question brings main's unresolved fine units to eight, rather than being
silently settled by ordinary non-PDT programs. Review and exact provenance
are recorded in `doc/source_audits/batch_018.json`.

The nineteenth batch integrates 18 independently reviewed ordinary
finalization-event programs representing 19 facets, with 14 still pending.
Old-value/RHS order, allocation replacement, local and BLOCK lifetimes,
whole-construct result timing and ordinary/elemental OUT entry have separate
conditions and nonvacuous observers. Sixteen cases are reference-validated;
IF/DO result cases retain source-only approval and unchanged whole-construct
oracles. GNU misses their callback, Flang finalizes in the header, and
LFortran already has an unexpected callback at consumer entry.

The coordinator verified 64 full-program countermodels over the 16
GNU-positive parents and the exact 44-site primitive guard matrix, then
independently rebuilt its driver and reran all 448 probes. Synthetic logs
are not successful automatic-finalization executions for IF/DO, and none of
these controls becomes another conformance case. The source/observer and
exact provenance decisions are in `doc/source_audits/batch_019.json`.

The nineteenth-batch measured whole-target checkpoint has **1,873 cases**:
**1,159 PASS, 709 XFAIL, four SKIPs and one NEEDS_ORACLE**.
All 1,855 prior IDs, fingerprints and target outcomes/phases are unchanged.
There are 77 catalogues, 403 requirements, 1,611 direct and four linked
facets, and 431 pending facets. All deallocation-owned, conditional
specification-expression and source-use followups remain explicit.

A separate coordinator-authored binding-reuse candidate, `6f064df`,
refreshes the four earlier proposals and adds the default-public connection.
Five draft links reuse six canonical cases without another program. Its
generator distinguishes direct, registered-linked and pending facets; only
three existing cases acquire changed requirement-metadata fingerprints,
with fresh observations and no input-byte changes. The candidate initially
remained outside main. Independent review found the five semantic connections
eligible but identified two generator defects: false connection prose after
removal/restoration, and silent omission of unknown explicit-map owners.
Correction `a9ec1bf` uses conditional/candidate prose and an exact current
link list, rejects unknown scoped owners, and exercises all 32 subsets
through real Registry collection/rendering. Its 81 regressions and fresh
nine-case observations did not substitute for independent correction
closeout. Both findings have now been independently closed, and batch021
explicitly renews the source, three metadata-bound cases, five connection
receipts and observational inventory.

The twentieth batch integrates **34 compile-only type-specifier cases**:
17 diagnostic inputs and 17 positive controls, representing 28 facets.
All 17 controls compile with GNU f2023; 23 cases are reference-validated and
11 negatives retain source-only approval. Empty-list/non-PDT/missing-value
conditions, keyword correspondence/order and complete C7100 dummy/selector/
allocation contexts remain distinct. No allocation or parameter-value
runtime effect is inferred from these admissions.

Twelve predicates were calibrated from actual native messages, with a
genuine current-fingerprint refresh and all original rows preserved.
Eighty-seven archived negative checks were independently replayed.
Uncredited generic recovery or conservative wording matches are not
automatically failures of the standard's minimum reporting capability.
Source and exact provenance are in `doc/source_audits/batch_020.json`.

The twentieth-batch measured whole-target checkpoint has **1,907 cases**:
**1,168 PASS, 734 XFAIL, four SKIPs and one NEEDS_ORACLE**.
All 1,873 prior IDs, fingerprints and target outcomes/phases are unchanged.
There are 78 catalogues, 414 requirements, 1,639 direct and four linked
facets, and 462 pending facets. All 31 remaining local facets, including
15 S-owned value/default/conversion effects, remain explicitly pending.

The twenty-first batch makes the five reviewed canonical connections
current without adding a conformance case. Two S7.5.5-007 outside-call pairs
retain their diagnostic/control ownership; two existing S7.5.2.2-001
runtime programs serve three permitted-call/default facets. Six unique
cases supply seven link-member occurrences, but each remains one scheduled
case per processor configuration. No passing linked effect is computed.

The twenty-first-batch measured checkpoint remains **1,907 cases: 1,168 PASS,
734 XFAIL, four SKIPs and one NEEDS_ORACLE**. Every prior case ID, input,
target outcome/phase and baseline line is unchanged; three metadata
fingerprints have explicit current renewals and the other 1,904 are
unchanged. There are **1,639 direct, nine current-linked and 457 pending
facets out of 2,105**. The 78 catalogues, 414 requirements and remaining
source gaps do not change. Complete connection, state-transition and
provenance decisions are in `doc/source_audits/batch_021.json`.

The twenty-second batch adds two shared unnamed-ENUM runtime programs for
seven finite common-kind/value/default/statement-partition/reset facets.
Five definitions supply 29 named INTEGER constants with independent literal
vectors. Flat/split forms are each checked against their own expected values;
KIND comparisons never cross definitions or assume a numeric identifier.
Forty-four separately bound wrong-oracle runs built successfully and failed
at their predicted guards, without becoming conformance negatives.

The twenty-second-batch measured checkpoint has **1,909 cases: 1,170 PASS,
734 XFAIL, four SKIPs and one NEEDS_ORACLE**. All 1,907 prior fingerprints,
outcomes, nine link receipts and baseline bytes are unchanged. There are
79 catalogues, 429 requirements, 1,646 direct and nine linked facets, and
514 pending facets out of 2,169. The 57 local followups include named enum,
BOZ, companion/representation and source-use work. Review and exact
provenance are in `doc/source_audits/batch_022.json`.

The twenty-third batch adds 28 reviewed compile-only constructor cases,
with 13 minimal repairs and 15 positive controls. Twenty newly authored
facets and two C7107 facets represented by existing programs now appear in
the detailed catalogue; those retained facets are not new executions.
All 17 controls, including two retained C7107 repairs, compile with GNU.
Three negatives remain source-only because their f2023 evidence is generic
recovery, incorrect component/parameter attribution or silent acceptance.

The twenty-third-batch measured checkpoint has **1,937 cases: 1,181 PASS,
751 XFAIL, four SKIPs and one NEEDS_ORACLE**. All 1,909 old inputs, IDs,
metadata and target outcomes/phases are unchanged. Four C7107 fingerprints
and three dependent links have explicit renewals; the other 1,905 case
fingerprints and six link receipts are unchanged. The baseline adds only
17 measured failures among new cases, preserving every old line.
There are 80 catalogues, 451 requirements, 1,668 direct and nine linked
facets, and 590 pending facets out of 2,267. Full source/cause and renewal
decisions are in `doc/source_audits/batch_023.json`.

The twenty-fourth batch registers the independently reviewed **7.8 array
constructor source catalogue**: 31 base units, 100 fine units and 26
requirements, with all **107 facets still pending**. It adds no test program
or completed facet. Typed/inferred characteristics, rank-one flattening,
statement-entity scope, ordinary DO execution, zero-trip character lengths
and BOZ representation conditions remain explicit future fixture gates.

The twenty-fourth-batch measured checkpoint has **1,937 cases: 1,181 PASS,
751 XFAIL, four SKIPs and one NEEDS_ORACLE**. Every case input, fingerprint,
review, outcome/phase, all nine link receipts and baseline bytes are
unchanged. Source context alone required an explicit inventory renewal;
a separate full frozen-target run retained all results. There are now
**81 catalogues, 477 requirements, 1,668 direct and nine linked facets,
and 697 pending facets out of 2,374**. Source accounting covers 1,553
base units; 4,920 base and eight fine units remain unresolved. The three
prior draft source catalogues are not silently approved. Source judgments,
preservation and measured evidence are in `doc/source_audits/batch_024.json`.

The twenty-fifth checkpoint combines two separately reviewed neighboring
packets. Three enumeration-type programs represent eight facets with
**source-only run contracts**: all nine original compiler attempts stopped
at syntax, and all 36 source-coded checks remain without native runtime or
sensitivity qualification. Their enumeration identities, access, ordinal
and named-member constructor oracles are retained without INTEGER substitutes.

The binary/octal packet adds 32 compile-only cases for 12 lexical facets:
24 isolated negatives and eight shared INTEGER DATA controls. Every control
compiles in all sampled configurations; GNU f2023 corroborates the four
truly empty-body diagnostics. Twenty negatives remain source-only. Flang's
14 additional exact token/character reports are f2018 observations, not
f2023 qualification. Generic recovery retains conservative noncredit rather
than being declared universal processor nonconformance.

The twenty-fifth-batch measured checkpoint has **1,972 cases: 1,189 PASS,
778 XFAIL, four SKIPs and one NEEDS_ORACLE**. All 1,937 prior case bindings,
reviews, outcomes/phases and nine link receipts are unchanged. Only 27
observed failures among the 35 new cases were added to the baseline.
There are **83 catalogues, 499 requirements, 1,688 direct and nine linked
facets, and 793 pending facets out of 2,490**. Source accounting covers
1,562 base units; 4,911 base and eight fine units remain unresolved.
The two source and 35 case reviews, exact historical/current joins and
explicit inventory renewal are in `doc/source_audits/batch_025.json`.

The twenty-sixth checkpoint integrates independently reviewed, non-executable
source-use inventory infrastructure. Explicit complete source sections
determine its denominator; missing and pending entries remain visible.
Targets stay pending and receive no new execution or coverage credit. The
committed registry is empty, not an approved assumed-term census.

Independent review found SULR-001: a rationale-only re-adjudication could
evade the report/baseline snapshot. The closed correction separately binds
the complete persisted review record, including hidden stale-record fields,
and uses one pre/post snapshot representation. Stable draft/stale inventories
still do not veto independently approved executions. These transaction
guarantees do not create a recursive semantic approval fingerprint.

The batch026 full target run has **1,972 cases: 1,189 PASS,
778 XFAIL, four SKIPs and one NEEDS_ORACLE**. All case, source, review, link,
execution-inventory and baseline bindings were unchanged in that checkpoint.
Its 83 catalogues, 499 requirements and 1,688 direct/nine linked/793 pending
facets were unchanged. Independent closeout and complete integration
evidence are in `doc/source_audits/batch_026.json`.

The twenty-seventh checkpoint is source-only: reviewed 8.3 automatic-object
and 8.4 initialization catalogues account for six base and 46 fine units,
with seven requirements and all **53 facets pending**. Exact entry-capture,
DATA/default, initial-value, overlap/shape, association and SAVE conditions
retain their implementation and oracle qualifications.

The corpus now has **85 catalogues, 506 requirements, 1,688 direct and nine
linked facets, and 846 pending facets out of 2,543**. Source accounting covers
1,567 base units; 4,906 base and eight fine units remain unresolved. All
1,972 case bindings, approvals, links and baseline bytes are unchanged.
Only source and observational-inventory reviews were renewed. No compiler
was rerun for this source-only registration: the last actual full report
remains batch026 and was not relabelled to the new source-context fingerprint.
The source and metadata evidence is in `doc/source_audits/batch_027.json`.

The twenty-eighth checkpoint adds five fully reviewed corrected
array-constructor runtime programs for ten facets. AVFR-001 is closed:
the fifteen rank observations now use real assumed-rank dummy data objects,
with SELECT RANK and size guards before element access, rather than invalid
direct RANK constructor-expression arguments. All 87 primitive literal
expectations and five completion counts are preserved.

All five programs run successfully on the frozen target. One GNU f2023
parent qualifies for reference validation; four programs remain source-only
with their failed GNU observations retained. The 35 wrong-oracle probes
demonstrate their intended failures; 57 of 60 rank probes do so. Three
target scalar-CHARACTER probes remain unqualified, not silently counted
as successful rank discrimination. Actual Flang f2018 evidence is not
promoted to f2023.

The twenty-eighth-batch measured checkpoint has **1,977 cases: 1,194 PASS,
778 XFAIL, four SKIPs and one NEEDS_ORACLE**. Every prior case binding,
review and outcome/phase, nine link receipts and baseline bytes are
unchanged. There are **85 catalogues, 506 requirements, 1,698 direct and
nine linked facets, and 836 pending facets out of 2,543**; source census
counts do not change. Source/oracle closeout, exact provenance and remaining
probe limitations are in `doc/source_audits/batch_028.json`.

The twenty-ninth checkpoint adds five reviewed local type-parameter capture
runs for seven S8.3-001 facets. Procedure and BLOCK entry, both CHARACTER
length declaration forms, post-undefinition observations without an undefined
source read, fresh entries and nested blocks have independent literal
length/payload/entry-count oracles. All five parents run with GNU f2023,
the frozen target and Flang f2018; all 39 bound wrong-oracle probes reach
their intended guards on GNU f2023.

The twenty-ninth-batch measured checkpoint has **1,982 cases: 1,199 PASS,
778 XFAIL, four SKIPs and one NEEDS_ORACLE**. Every prior case binding,
review/outcome/phase, nine links and baseline bytes are unchanged. There
are **85 catalogues, 506 requirements, 1,705 direct and nine linked facets,
and 829 pending facets out of 2,543**. All nine C814 and two other local
entry-capture facets remain pending; source census counts do not change.
Complete source/oracle/probe and integration evidence is in
`doc/source_audits/batch_029.json`.

The thirtieth checkpoint registers the reviewed 8.1/8.2 source and integrates
the C801 metadata migration with five exact duplicate-attribute deletion
controls. Six retained execution IDs and their original program bodies remain;
the valid run gains only a facet header. Five negative review keys become
per-execution keys, the valid key is explicitly renewed, and the old invalid
group remains retired history rather than approval of the new bindings.

Independent review closed all three C801 findings. Valid-key renewal and
generated lifecycle states are no longer tied to permanent draft assumptions.
The corrected predicates reject the demonstrated unsupported/Internal
wrappers: the same 270-vector matrix has zero false credits, versus 105
with the old contracts. Four genuine Flang warning noncredits remain an
explicit sidecar limitation, not a claim that the compiler did not report.
Current evidence joins five freshly observed negative rows with six unchanged
positive rows; all eleven have qualifying GNU f2023 evidence. No combined
invocation or f2023 Flang configuration is invented.

The thirtieth-batch measured checkpoint has **1,987 cases: 1,204 PASS,
778 XFAIL, four SKIPs and one NEEDS_ORACLE**. All 1,982 prior outcomes and
phases, 1,976 unaffected case fingerprints, nine links and baseline bytes
are preserved. There are **87 catalogues, 529 requirements, 1,711 direct
and nine linked facets, and 947 pending facets out of 2,667**. Source
accounting covers 1,576 base units; 4,897 base and eight fine units remain
unresolved. The new source exposes 118 pending 8.2 facets rather than hiding
them behind the six represented C801 facets. Exact source, cause, provenance,
retired-history and integration evidence is in
`doc/source_audits/batch_030.json`.

The thirty-first checkpoint is source-only: reviewed ALLOCATABLE and
ASYNCHRONOUS catalogues account for seven base and 34 fine units.
ALLOCATABLE remains definition-only; three ASYNCHRONOUS requirements
retain all **22 facets pending**. Exact scoped predicates, implicit
attribute routes, completion/definedness, BLOCK identity, subobjects and
processor-qualified foreign communication remain separate evidence plans.

The thirty-first-batch corpus has **89 catalogues, 532 requirements, 1,711 direct and nine
linked facets, and 969 pending facets out of 2,689**. Source accounting
covers 1,583 base units; 4,890 base and eight fine units remain unresolved.
All 1,987 case bindings, 1,946 stored review records, nine links and baseline
bytes are unchanged. Only source and observational-inventory reviews were
renewed. The last actual full compiler report remains batch030 with its
original 87-catalogue context; it was not relabelled as a new run.
Exact source and preservation evidence is in `doc/source_audits/batch_031.json`.

The thirty-second checkpoint is also source-only: reviewed BIND data/common
source accounts for nine base and 37 fine units, with seven requirements
and all **55 facets pending**. Companion identity, ISO kind availability,
variable versus C-counterpart criteria, COMMON membership, label semantics
and the bound-common SAVE effect retain their separate evidence gates.
The actual successor is CODIMENSION8.5.6, not the earlier CONTIGUOUS shorthand.

There are now **90 catalogues, 539 requirements, 1,711 direct and nine
linked facets, and 1,024 pending facets out of 2,744**. Source accounting
covers 1,587 base units; 4,886 base and eight fine units remain unresolved.
All 1,987 case bindings, 1,946 stored reviews, nine links and baseline bytes
are unchanged. One source review and the separate observational-inventory
review were written. Batch030 remains the last actual full compiler report
with its original context, not a new90-catalogue run. Details are in
`doc/source_audits/batch_032.json`.

The thirty-third checkpoint integrates the first independently reviewed
finite source-use inventory: `R402.declaration-name-uses-8.2`. All127
units of8.2 are classified, with30 mapped and97 not applicable. Its31
contextual records retain seven physical parent occurrences, distinguishing
assumed `function-name` from explicitly defined `object-name`. The original
502 numbered production heads were checked independently of the known-rule
whitelist; this is not global paragraph/list/table ratification.

The inventory is current but grants **no execution or facet-completion
credit**. R402's whole-standard census remains pending. Corpus source and
facet counts and all1,987 case bindings are unchanged. Literal empty-registry
wording in current attribute documentation was made timeless, with explicit
source and execution-context renewal; the old compiler report remains
untouched. Details are in `doc/source_audits/batch_033.json`.

The thirty-fourth checkpoint adds ten independently reviewed C814 compile
cases for five automatic-object SAVE facets. Three exact SAVE-only repairs,
three prior constant-expression inquiry controls and the no-list SAVE
admission retain complete valid contexts. ASFR-001's nine demonstrated
Internal-wrapper false credits and both directions of cross-owner
pending-count test assumptions are closed without changing the Fortran
sources or importing the separate shared-parser candidate.

All ten cases have qualifying GNU f2023 evidence. Six compile on the frozen
target; four demonstrated failures are explicitly added to the baseline,
including the source-valid no-list SAVE abort. The current measured
checkpoint has **1,997 cases: 1,210 PASS, 782 XFAIL, four SKIPs and one
NEEDS_ORACLE**. All1,987 prior outcomes, bindings and input hashes remain,
as do nine links and the current R402 inventory. There are **1,716 direct,
nine linked and1,019 pending facets out of2,744**; source census counts
are unchanged. Four C814 and two entry-capture facets remain pending.
Evidence and exact correction/provenance limits are in
`doc/source_audits/batch_034.json`.

The thirty-fifth checkpoint registers independently reviewed CODIMENSION
source:26 base and85 fine units,22 requirements and all **80 facets
pending**. The empty structural parent receives no artificial catalogue.
Rank/corank, allocation/association, undefined properties, permitted
inquiries, entry capture and image/team boundaries remain distinct plans.
No compiler, launcher or new multi-image execution is inferred.

The corpus now has **93 catalogues, 561 requirements, 1,716 direct and nine
linked facets, and1,099 pending facets out of2,824**. Source accounting
covers1,600 base units;4,873 base and eight fine units remain unresolved.
All1,997 case bindings,1,956 stored reviews, nine links, the current R402
inventory and baseline bytes are unchanged. Three source reviews and one
execution-context renewal are explicit; batch034 remains the last actual
full main run with its own90-catalogue context. See
`doc/source_audits/batch_035.json`.

The thirty-sixth checkpoint integrates corrected C815 metadata and five
syntax-only second-statement deletion controls. All31 source lines,
comments and padding are retained. The 210 demonstrated unsupported/Internal
false credits are closed; historical whole-line controls remain valid old
Fortran evidence, not relabelled current inputs. All eleven changed
fingerprints have fresh GNU f2023 observations.

Six previously current canonical links genuinely became source-stale under
the new8.5.2 catalogue. Their source prerequisites and six link reviews were
explicitly renewed, preserving every canonical input, role and phase and
the other three receipts. Retired C815 invalid-group history remains separate
from its five new per-execution review keys.

The current measured checkpoint has **2,002 cases: 1,215 PASS,
782 XFAIL, four SKIPs and one NEEDS_ORACLE**. Every prior execution's
outcome and phase is unchanged, and all five new controls compile on the
target. There are **95 catalogues, 568 requirements, 1,722 direct and nine
linked facets, and1,148 pending facets out of2,879**. Source accounting
covers1,607 base units;4,866 base and eight fine units remain unresolved.
Baseline bytes and the current R402 inventory are unchanged. Exact native,
historical, repair and renewal evidence is in `doc/source_audits/batch_036.json`.

The thirty-seventh checkpoint adds seven independently reviewed C819
compile cases: one module admission and three wrong-context declarations
with exact BIND-only repairs. The protected C814 lifecycle test now
preserves unrelated inventory members and unreviewed blockers rather than
forcing whole-suite approval. No source, native row or foreign review was
changed to make that test pass.

All seven cases have GNU f2023 corroboration. Four compile on the frozen
target; three silent-acceptance failures are explicitly baselined.
The current measured checkpoint has **2,009 cases: 1,219 PASS,
785 XFAIL, four SKIPs and one NEEDS_ORACLE**. Every prior outcome,
binding, input hash, link receipt and current R402 snapshot is unchanged.
There are **1,726 direct, nine linked and1,144 pending facets out of2,879**;
source counts do not change. The remaining three C819 and48other local
facets stay pending. Exact source, repair, compatibility and native evidence
is in `doc/source_audits/batch_037.json`.

The thirty-eighth checkpoint is source-only: reviewed CONTIGUOUS source
accounts for eight base and44 fine units, with five requirements and all
**36 facets pending**. Attribute eligibility, actual contiguity, simple
syntax, inquiry availability and residual processor choices remain
separate; no stride/address/size formula or temporary/copy-count oracle is
introduced.

There are now **96 catalogues, 573 requirements, 1,726 direct and nine
linked facets, and1,180 pending facets out of2,915**. Source accounting
covers1,614 base units;4,859 base and eight fine units remain unresolved.
All2,009 case bindings,1,973 stored reviews, nine links, the current R402
snapshot and baseline bytes are unchanged. One source and one execution
context review were written; batch037 remains the last actual full main
run with its own95-catalogue context. See `doc/source_audits/batch_038.json`.

The thirty-ninth checkpoint is also source-only: DIMENSION general and
explicit-shape source accounts for18 base and87 fine units, with15
requirements and all **78 facets pending**. Scalar/list/vector grammar,
constant size versus constant values, broadcasting, empty extents and
entry capture retain their separate premises. C831 main/module reporting
overlap with implicit SAVE remains a gate, not an isolated negative.
One informative-note rationale was clarified to state the exact maximum
rank formula.

There are now **98 catalogues, 588 requirements, 1,726 direct and nine
linked facets, and1,258 pending facets out of2,993**. Source accounting
covers1,623 base units;4,850 base and eight fine units remain unresolved.
All2,009 case bindings,1,973 stored reviews, nine links, the current R402
snapshot and baseline are unchanged. Two source reviews and one inventory
source-context renewal create no new compiler observation; batch037 is
still the last actual full main run. See `doc/source_audits/batch_039.json`.

The fortieth checkpoint integrates the shared SHORT diagnostic guard after
independent closure of SIGR-001/002/003 and the bounded unlocated-content
edge. Extraction and native-Internal detection use the same first unshielded
header, normalize severity whitespace consistently, and do not borrow
quoted examples. Application output remains outside compiler classification;
fatal exits, message wording, codes and warning policies are unchanged.

The new actual full main run retains **2,009 cases: 1,219 PASS, 785 XFAIL,
four SKIPs and one NEEDS_ORACLE**, with3,062 case command traces validated.
All verdicts, phases, inputs, approvals,98 catalogues, nine links, the R402
snapshot and baseline are unchanged. The12 new harness methods do not add
Fortran cases or facets. The complete Python suite has674 methods; the full
parser-file selector has89, distinct from the independent76-method subset.
Batch040 is now the latest actual main run with its98-catalogue context;
neither the older1,987-case candidate report nor batch037 was relabelled.
Exact closeout and execution evidence is in `doc/source_audits/batch_040.json`.

The forty-first checkpoint reaches **100 detailed catalogues** by integrating
independently reviewed assumed/deferred-shape source:14 base and63 fine
units,11 requirements and all49 new facets pending. Rank, lower bounds,
effective extents, inactive properties, inquiry exceptions and allocation/
association/lifetime conditions stay distinct. The pointer-bound permission
list retains explicit canonical mechanism/source follow-ups; classifying
the text does not claim those mechanisms are tested.

There are now **599 requirements, 1,726 direct and nine linked facets, and
1,307 pending facets out of3,042**. Source accounting covers1,633 base units;
4,840 base and eight fine units remain unresolved. All2,009 case bindings,
1,973 stored reviews, nine links, the R402 snapshot, parser and baseline
are unchanged. Only two source reviews and one inventory-context renewal
were written. Batch040 remains the last actual full run with its98-catalogue
context, not a fabricated100-catalogue execution. See
`doc/source_audits/batch_041.json`.

The forty-second checkpoint adds explicit `positive_control_facets` for
source-supported controls within supplementary effect requirements.
Direct and canonical cases share the same per-facet role validation.
Independent finding ECFR-001 caught graph reapproval after a control
designation moved or disappeared; the corrected guard rejects that path
before changing a review. Marked targets retain an explicit control
pattern, and run controls never become runtime-effect passes.

No real requirement opts in yet. All2,009 case bindings,100 catalogues,
1,973 stored reviews, nine links, R402 and inventory snapshots and the
baseline remain unchanged. The corrected author's full690-method run
and current main's247-method role/parser selection have distinct recorded
contexts. No compiler invocation or new conformance facet is claimed;
batch040 remains the last actual full main execution. BIND-common SAVE
authoring may now resume as a separate reviewed source/fixture task.
See `doc/source_audits/batch_042.json`.

The forty-third checkpoint adds independently reviewed assumed-size and
implied-shape source:17 base and70 fine units,15 requirements and all59
new facets pending. Conceptual sequence size is not an available whole
array inquiry. Safe reads remain partial evidence; zero-length character
maximums and distinct C-character-kind reconciliation stay explicit gates.
Named-constant rank, initialization, bound constancy and empty-dimension
inquiry rules are not replaced with assumed-size or allocation semantics.

The corpus now has **102 catalogues, 614 requirements, 1,726 direct and
nine linked facets, and1,366 pending facets out of3,101**. Source accounting
covers1,642 base units;4,831 base and eight fine units remain unresolved.
All2,009 case bindings,1,973 stored reviews, nine links, R402, parser,
role support and baseline are preserved. Two source reviews and one
inventory-context renewal create no new compiler run; batch040 retains
its actual98-catalogue context. See `doc/source_audits/batch_043.json`.

The forty-fourth checkpoint adds opt-in exact diagnostic causes and actual
staged-source attribution. Quoted examples inside unrelated errors cannot
satisfy an exact selector, and foreign files cannot borrow a matching
basename. Existing nonfatal, source-span, code and native-failure gates
remain conjunctive; unbound parsing and external rejection policies retain
their separate contracts.

A new actual full main run, using the same frozen Fortran and Apple-clang
configuration as batch040, preserves **2,009 cases: 1,219 PASS, 785 XFAIL,
four SKIPs and one NEEDS_ORACLE**. All3,062 case command traces and the
complete observational projection were validated. The current combined
precision/role selection has320 passing methods; the author's689-method
full Python run retains its own100-catalogue context. No real exact
selector, case, facet, approval or baseline entry is added here.
Batch044 is the latest actual full run with102 catalogues. See
`doc/source_audits/batch_044.json`.

The forty-fifth checkpoint integrates the12 corrected C830 compile cases
after independent closure of both cause/origin false-credit findings.
Four invalid categories have exact CONTIGUOUS-only repairs; four additional
admissions cover the eligible categories, including an ALLOCATABLE
assumed-rank dummy. The eight positives remain compile controls, not
runtime contiguity effects. Exact predicates preserve genuine nonfatal
reporting and actual source attribution without prescribing English.

The measured corpus is now **2,021 cases: 1,227 PASS, 789 XFAIL,
four SKIPs and one NEEDS_ORACLE**. All2,009 prior outcomes and bindings
are unchanged; only the four reviewed target reporting failures were added
to the baseline. There are **1,733 direct, nine linked and1,359 pending
facets out of3,101**; source counts are unchanged. All733 Python methods
passed, and the new full main report has3,074 validated case command traces.
The assumed-size anchor facet and28S-owned CONTIGUOUS facets remain pending.
See `doc/source_audits/batch_045.json`.

The forty-sixth checkpoint adds two complete BIND-common SAVE programs.
An actual writer and reader are the only scopes declaring the block;
literal11/13 and17/19 values survive complete returns. The confirmation
differs only by two block SAVE statements. Its first real
`positive_control_facets` designation has independent source approval:
the confirmation is a run control, not a second runtime effect.

Both programs were independently reexecuted with target/GNU/Flang, and
all72 full-program sensitivity records were checked through their actual
inputs and216 command traces. The full main run now has **2,023 cases:
1,229 PASS, 789 XFAIL, four SKIPs and one NEEDS_ORACLE**. All2,021
previous outcomes and bindings and the baseline are unchanged. The corpus
has **1,735 direct, nine linked and1,357 pending facets out of3,101**;
source counts remain unchanged. The746-method Python suite passed, and
the qualified execution projection counts exactly one new effect pass
and one new positive-control pass. See `doc/source_audits/batch_046.json`.

The forty-seventh checkpoint integrates assumed-rank source, completing
source cataloguing of the shape-category sequence without claiming its
runtime facets are complete. Five base and39 fine units supply five
requirements and all32 new facets pending. Name-use permissions retain
intrinsic/state/argument prerequisites; C841 actual-array conditions and
the pointer-association terminology remain explicitly qualified.

There are now **103 catalogues, 619 requirements, 1,735 direct and nine
linked facets, and1,389 pending facets out of3,133**. Source accounting
covers1,643 base units;4,830 base and eight fine units remain unresolved.
All2,023 case bindings,1,987 stored reviews, nine links, R402, the BIND
control designation and baseline remain unchanged. Source and inventory
context review add no compiler observation; batch046 retains its actual
102-catalogue context. See `doc/source_audits/batch_047.json`.

The forty-eighth checkpoint supplies reviewed `additional_spans` for exact
disjoint diagnostic anchors. A report must fit wholly within one declared
interval; gaps and ranges bridging two intervals remain unqualified. The
primary marker, common cause, staged source, nonfatal and failure gates
are preserved. The held C830 header4/declaration6 relation was exercised
without merging it into a4..6span or changing the original program.

No real fixture opts in yet, and no case, facet, approval or baseline entry
is added. All2,023 current case bindings,103 catalogues,1,987 reviews, nine
links, R402 and inventory snapshots remain unchanged. The current357-method
combined selection and the author's697-method full run have distinct
recorded contexts; batch046 remains the latest actual full main execution.
See `doc/source_audits/batch_048.json`.

The forty-ninth checkpoint adds two actual local-array bound-capture
programs for six facets: procedure/BLOCK entry, source redefinition and
undefinition, fresh activations and nested BLOCK lifetimes. Independent
literal oracles and complete-program probes preserve valid semantics
instead of weakening them to match the target. Both target programs reach
runtime and fail their first post-redefinition UBOUND check.

All477 full-program probes reached runtime. GNU has159 qualified reference
sensitivity results and Flang159 supplementary results; the target has
**zero qualified sensitivity** because its unchanged parents fail.
The full corpus is **2,025 cases: 1,229 PASS, 791 XFAIL, four SKIPs
and one NEEDS_ORACLE**. All2,023 prior results and bindings are preserved,
and only the two reviewed runtime failures were added to the baseline.
There are **1,741 direct, nine linked and1,383 pending facets out of3,133**;
source counts are unchanged. The767-method Python suite passed.
See `doc/source_audits/batch_049.json`.

The fiftieth checkpoint registers the original held C830 assumed-size
negative and its minimal repair: the sole source change removes
`, contiguous`. GNU's header line4 and Flang's declaration line6 are
separate allowed anchors, never a widened4..6range. Complete causes and
live staged-source identity still qualify every diagnostic.

All fourteen current C830 cases have fresh independent observations and
explicit main approval. The twelve old source/manifest pairs are unchanged,
but their requirement-bound fingerprints genuinely changed; their reviews
were renewed, not silently rebound. All2,013 other old case bindings and
all2,025 prior outcomes are preserved. The full corpus is **2,027 cases:
1,230 PASS, 792 XFAIL, four SKIPs and one NEEDS_ORACLE**. Only the new
missing-report failure was added to the baseline. The770-method Python
suite passed. There are **1,742 direct, nine linked and1,382 pending facets
out of3,133**; source counts are unchanged. The finite eight-facet C830
matrix is represented, but all28 local S facets remain pending and no
runtime contiguity credit is claimed. See `doc/source_audits/batch_050.json`.

The fifty-first checkpoint adds eight C834 compile cases for three finite
ordinary-array facets. POINTER/ALLOCATABLE are crossed with scalar and
constant size-one vector bounds; each negative is repaired only to a
single deferred-shape colon. The two same-attribute control source pairs
are byte-identical and retain four repair relationships, not extra
semantic effects. Original source, exact causes, staged origins and all
2,144 stored countermodel traces were independently checked.

GNU f2023 corroborates all eight contracts. The target passes six case
judgments but reports only an unrelated scalar-bound complaint for the two
vector negatives; those remain failures. Flang's genuine C834 reports and
additional scalar-only complaints are preserved as f2018 supplementary
evidence. The full corpus is **2,035 cases: 1,236 PASS, 794 XFAIL,
four SKIPs and one NEEDS_ORACLE**. All2,027 old results/bindings and
1,991 old reviews are unchanged; only the two reviewed reporting failures
were added to the baseline. The785-method Python suite passed. There are
**1,745 direct, nine linked and1,379 pending facets out of3,133**;
source counts are unchanged. Three other C834 and all23 R822/S facets stay
pending. See `doc/source_audits/batch_051.json`.

The fifty-second checkpoint registers the already independently reviewed
7.5.8 half of the earlier value/specifier source packet, without overwriting
the newer7.5.9 material. Two original paragraphs and14 fine units supply
three requirements, all13 facets pending. Pointer association, allocated-only
characteristics and ordinary component values remain distinct. The normative
value-set definition is accounted without inventing a no-op execution.

The current corpus has **104 catalogues, 622 requirements, 1,745 direct,
nine linked and1,392 pending facets out of3,146**. Source accounting covers
1,645 base units;4,828 base and eight fine units remain unresolved. All2,035
case bindings,1,999 stored reviews, nine links, R402 and the baseline are
unchanged. Source and inventory context review add no compiler observation:
batch051 retains its actual103-catalogue/619-requirement full-run context.
The172-method source/evidence selection passed. See
`doc/source_audits/batch_052.json`.

The fifty-third checkpoint registers independently reviewed EXTERNAL and
INTENT source:23 base units,104 fine units,21 requirements and all97 new
facets pending. Nine numbered units were already accounted; the actual
base-unit reduction is14. Pointer association, target data, OUT entry
undefinedness, actual-argument requirements and invocation-statement
interference remain distinct. Continued note4.2 and the global always-defined
zero-size/zero-length boundary are retained without new trap/value oracles.

The corpus now has **106 catalogues, 643 requirements, 1,745 direct,
nine linked and1,489 pending facets out of3,243**. Source accounting covers
1,659 base units;4,814 base and eight fine units remain unresolved.
All2,035 case bindings,1,999 stored reviews, nine links, R402 and the baseline
are unchanged. Only source and inventory context are renewed; batch051
remains the actual last full run in its103-catalogue/619-requirement context.
The172-method source/evidence selection passed. See
`doc/source_audits/batch_053.json`.

The fifty-fourth checkpoint registers independently reviewed INTRINSIC
and OPTIONAL source: six base units,24 fine units, four requirements and
all23 new facets pending. Two numbered units were already accounted, so
four additional base units are resolved. Specific-intrinsic eligibility,
generic procedure-class constraints and their causal overlaps stay explicit.
OPTIONAL presence is not equated with allocation, pointer association or
having an effective argument; conditional-NIL and absent-use rules retain
their full independent constraints.

There are now **108 catalogues, 647 requirements, 1,745 direct, nine linked
and1,512 pending facets out of3,266**. Source accounting covers1,663 base
units;4,810 base and eight fine units remain unresolved. All2,035 cases,
1,999 stored reviews, nine links, R402 and the baseline are preserved.
Source and inventory context reviews add no compiler observation and do
not relabel batch051's actual full-run context. The172-method source/evidence
selection passed. See `doc/source_audits/batch_054.json`.

The fifty-fifth checkpoint closes the complete intrinsic-assignment
prototype's **source-review** gate. Independent review covered all26 base
units,16 fine units,32 requirements and144 facets in10.2.1.3, not just the
component-assignment paragraphs. The definitions, accounting and all six
pending facets are unchanged; source status is now content-bound reviewed.

This adds no case, facet, canonical connection or compiler observation.
All2,035 case bindings and1,999 stored reviews remain unchanged, including
the assignment population's36 reference-validated, four source-reviewed
and one needs-oracle records. Real BOZ remains **NEEDS_ORACLE**, and all13
proposed7.5.8connections still need independent source/basis/fixture/oracle
review. The view labels its prototype compiler snapshot as historical.
Corpus counts remain108catalogues/647requirements/1,512pending facets;
the179-method metadata selection passed. See
`doc/source_audits/batch_055.json`.

The fifty-sixth checkpoint registers two CONTIGUOUS dummy runtime effects
after independent source/oracle review and CIDR-001/002 correction closeout.
The generator now preserves supplied unselected lifecycle state instead
of forcing every other facet pending, and its foreign-state prose is
timeless. The Fortran programs and literal oracles are unchanged. A
limitation-text change genuinely changed both fingerprints, so all six
parents and124 attempted full-program probes were freshly observed.

The assumed-shape case has GNU f2023 corroboration; the assumed-rank case
remains source-reviewed because GNU fails a payload check and Flang's
successful f2018 runs are supplementary. Neither target case passes:
one fails contiguity at runtime and one encounters a compile ICE.
The26 unrun target rank probes remain UNTESTED; only24 GNU probes and50
supplementary Flang probes qualify sensitivity.

The full corpus is **2,037 cases: 1,236 PASS, 796 XFAIL, four SKIPs and
one NEEDS_ORACLE** in the actual108-catalogue/647-requirement context.
All2,035 prior results/bindings and the fourteen-case C830 contract are
preserved; only the two reviewed target failures were added to the baseline.
There are **1,747 direct, nine linked and1,510 pending facets out of3,266**;
source counts are unchanged. The800-method Python suite passed. No new
target runtime-effect pass is claimed. See `doc/source_audits/batch_056.json`.

The fifty-seventh checkpoint registers13 independently reviewed singleton
runtime connections for7.5.8 over **five unchanged canonical programs**.
Each link keeps its S10primary owner, source/role/phase and complete-program
oracle. Pointer association, allocated-only characteristics and ordinary
values have separate finite proofs; no p2classifier, copied program,
multi-program fragment combination or extra execution is created.

The five parents were independently reexecuted, then observed again on main
under the current connection context:15 processor attempts and30 actual
compile-link/run traces, not13 executions per configuration. GNU f2023 and
Flang f2018 pass all five under their unchanged required-standard contracts;
LFortran passes four and fails S024's array-pointer guard. **All four pointer
connections retain that complete-parent failure.** The shared reporter
still does not compute passing linked-effect aggregates.

There remain **2,037 cases**, with **1,747 direct,22 current linked and1,497
pending facets out of3,266**. All existing case fingerprints/reviews, nine
old link records, R402 and the baseline are unchanged. The192-method
source/evidence selection passed. This was a selected observation, not a
replacement for batch056's full run or its original nine-link context.
See `doc/source_audits/batch_057.json`.

The fifty-eighth checkpoint registers independently reviewed PARAMETER and
POINTER source:12 base units,49 fine units, eight requirements and all38
new facets pending. Four numbered units were already accounted; the actual
reduction in unresolved base units is eight. Named-constant expression and
ordering rules, pointer-entity exclusions, named-procedure EXTERNAL routes
and association/target/value/lifetime distinctions retain their exact gates.

There are now **110 catalogues, 655 requirements, 1,747 direct,22 linked
and1,535 pending facets out of3,304**. Source accounting covers1,671 base
units;4,802 base and eight fine units remain unresolved. All2,037 case
bindings,2,001 case reviews,22 current links, R402 and the baseline are
unchanged. This adds no compiler observation and does not relabel either
batch056's full-run context or batch057's selected observations. The192-method
source/evidence selection passed. See `doc/source_audits/batch_058.json`.

The fifty-ninth checkpoint registers four C851 compile cases for three
ordinary OPTIONAL eligibility facets. Complete data and nonpointer-procedure
nondummy declarations are repaired only by dummy-list insertion. GNU f2023
corroborates all four contracts; Flang's actual f2018 warnings are narrowly
calibrated supplementary evidence. The target silently accepts both invalid
declarations, so those reporting failures remain explicit.

The first full Python run exposed a fixed four-foreign-link assumption in
the earlier type-bound regression. It now preserves the actual foreign
records and effective fingerprints across all32owned subsets, rather than
replacing four with seventeen. The failed log and initial native report are
retained, and both full jobs were repeated after this test-only correction.

The final full corpus is **2,041 cases: 1,238 PASS, 798 XFAIL, four SKIPs
and one NEEDS_ORACLE**, in the actual110-catalogue/655-requirement/22-link
context. All2,037 prior outcomes and bindings are preserved; only the two
reviewed reporting failures were added to the baseline. There are
**1,750 direct,22 linked and1,532 pending facets out of3,304**; source
counts are unchanged. All837 Python tests pass. One other C851 facet and
all seven OPTIONAL S facets remain pending. See `doc/source_audits/batch_059.json`.

The sixtieth checkpoint adds two independently reviewed assumed-rank runtime
effects. A genuine `INTEGER, INTENT(IN) :: x(..)` observer sees ranks0/1/2
from named scalar/vector/matrix actuals and ranks1/2 from zero-sized arrays.
Literal oracles, entry/category/return/check totals and exact completion
output do not substitute a fixed-rank observer or read empty-array elements.
All25whole-program mutations were independently reconstructed;75fresh
processor probes reached their intended failures after six passing parents.

There are now **2,043 registered cases**, with **1,752 direct,22 current linked
and1,530 pending facets out of3,304**. Both new target cases and GNUf2023
references pass; actualFlangf2018passes remain supplementary. The current
main selection contains two cases, six processor executions and18commands,
not a new full-suite run. Batch059 remains the last actual2,041-case full
observation. All prior case bindings/reviews,22links,R402and the baseline
are preserved;43focused metadata/lifecycle checks pass. Thirty local facets
remain pending, including four other S1facets. Source accounting is unchanged.
See `doc/source_audits/batch_060.json`.

The sixty-first checkpoint registers independently reviewed PROTECTED/SAVE
source:15base units,80fine units,12requirements and90new pending facets.
Seven numbered units were already accounted; the actual reduction in
unresolved base units is eight. Protection, accessibility, defining contexts,
pointer association, retained state, scope and lifetime stay distinct.
SAVE never repairs a dead target or internal-procedure host instance.

The corpus remains **2,043 cases**, now with **112catalogues,667requirements,
1,752direct,22linked and1,620pending facets out of3,394**. Source accounting
covers1,679base units, with4,794base and eight fine units unresolved.
All prior case bindings,2,007reviews,22links,R402and the baseline are
unchanged. The192-method metadata selection passes. No compiler invocation
is added, and batch059's full report and batch060's selected observations
retain their original contexts. See `doc/source_audits/batch_061.json`.

The sixty-second checkpoint completes independent11.4source review without
changing the existing STOP calibration. All10base and53fine units are
classified; two previously unresolved base units and two fine units are
resolved. Eight new requirements add38pending facets. Required IEEE
warnings/ERROR_UNIT and QUIET suppression remain distinct from recommended
code output/status mappings and processor-interface qualification.

The corpus remains **2,043cases**, with **112catalogues,675requirements,
1,752direct,22linked and1,658pending facets out of3,432**. There are
**4,792unresolved base and six fine units**. The complete S11.4-001/profile
contract, all case bindings/reviews,22links,R402,baseline and foreign18.3.7
view bytes remain unchanged. The177-method metadata/profile selection
passes; no compiler invocation is added. Readable source-status banners
now reflect their recorded review rather than the author-stage draft.
See `doc/source_audits/batch_062.json`.

The sixty-third checkpoint registers independently reviewed RANK-clause and
VOLATILE source:14base/78fine units,11requirements and51pending facets.
Eight base units are newly accounted after six already-counted numbered
units. Rank-zero roles, constant inquiries, processor limits and conditional
array categories stay distinct. VOLATILE's recommendations do not become
mandatory visibility or timing tests; actual coarray and subobject
conditions retain their canonical owners.

There remain **2,043cases**, now with **114catalogues,686requirements,
1,752direct,22linked and1,709pending facets out of3,483**. Source accounting
covers1,689base units;4,784base and six fine units remain unresolved.
All prior case bindings/reviews,22links,R402andbaseline are preserved.
The172-method metadata selection passes, with no compiler invocation or
historical-report relabelling. See `doc/source_audits/batch_063.json`.

The sixty-fourth checkpoint registers independently reviewed TARGET/VALUE
source at the correct8.5.18/.19 sections:11base/48fine units, seven
requirements and37pending facets. The initial section-title guard stopped
before authoring; its blocker receipt is retained byte-for-byte. Six base
units are newly accounted after five numbered units already counted.
Target eligibility, subobject inheritance, pointer lifetime, anonymous VALUE
effective arguments and interoperable dummy restrictions stay distinct.

There remain **2,043cases**, now with **116catalogues,693requirements,
1,752direct,22linked and1,746pending facets out of3,520**. Source accounting
covers1,695base units;4,778base and six fine units remain unresolved.
All prior case bindings/reviews,22links,R402andbaseline are preserved.
The172-method metadata selection passes; no compiler invocation, automatic
canonical reuse or duplicated VALUE copy-effect requirement is added.
See `doc/source_audits/batch_064.json`.

The sixty-fifth checkpoint registers four C839/C840 compile cases for two
finite exclusions. A nondummy assumed-rank declaration is repaired only by
dummy-list insertion; direct `PRINT *, x` is repaired only to
`PRINT *, RANK(x)` in an otherwise identical complete program. Independent
review accepts the target's exact located PRINT prohibition, not generic
unsupported-feature wording. Flang's actualf2018silent acceptance remains
a reporting failure; GNUf2023corroborates all four cases.

The corpus is now **2,047cases**, with **1,754direct,22linked and1,744pending
facets out of3,520**; source counts are unchanged. The current selection has
four targetPASS results and12compile records, not a new full-suite run.
Two valid controls are qualified conforming admissions; two diagnostic-only
successes are not runtime effects or additional qualified valid members.
An auxiliary verifier initially confused those counts; the production
report was already correct and remains immutable. The56-method focused
selection passes, including the independently reviewed standalone-generator
test-scope correction. All prior case bindings,22links,R402and the failure
baseline survive. See `doc/source_audits/batch_065.json`.

The sixty-sixth checkpoint registers independently reviewed ALLOCATABLE and
ASYNCHRONOUS statement source: six base/24fine units, three numbered
requirements and29pending facets. Three base units are newly accounted;
the other three were already counted numbered rules. Statement syntax
and scoped attribute identity remain distinct from allocation, I/O and
communication operations. Neither paragraph creates a duplicate S classifier.

There remain **2,047cases**, now with **118catalogues,696requirements,
1,754direct,22linked and1,773pending facets out of3,549**. Source accounting
covers1,698base units;4,775base and six fine units remain unresolved.
All prior case bindings,2,011reviews,22links,R402andbaseline are preserved.
The172-method metadata selection passes; this source-only registration
adds no compiler invocation and does not relabel batch065's selected
observations or batch059's full report. See `doc/source_audits/batch_066.json`.

The sixty-seventh checkpoint adds two independently reviewed SAVE runtime
effects. An explicitly saved INTEGER local without an initializer retains
11then17 across three actual RETURNs. A second program proves sharing while
the outer recursive instance remains active: the inner instance reads11
and writes17, which the resumed outer instance reads directly. Independent
snapshots and lifecycle/check totals make missing work observable.

All50wrong-oracle and12omission programs were independently reconstructed;
186fresh processor runs reached the intended failures after six passing
parents. No undefined SAVE-removed program is used. The current main
selection adds two target/GNUf2023qualified effects, while actualFlangf2018
passes remain supplementary. This is not a new full-suite result.

There are now **2,049cases**, with **1,756direct,22linked and1,771pending
facets out of3,549**; source counts are unchanged. All2,047prior case
bindings,2,011reviews,22links,R402andbaseline survive. The later readable
source-status header is preserved when composing the new SAVE view.
The41-method focused selection passes. Six other S1facets and24other
local SAVE facets remain pending. See `doc/source_audits/batch_067.json`.

The sixty-eighth checkpoint registers independently reviewed BIND and
CODIMENSION statement source: eight base/30fine units, five numbered
requirements and38pending facets. Three base units are newly accounted;
five numbered units were already counted. NAME presence remains distinct
from label existence, a COMMON block from its members, and ordinary rank
from corank. Declaration admission supplies no C ABI or multi-image result.

There remain **2,049cases**, now with **120catalogues,701requirements,
1,756direct,22linked and1,809pending facets out of3,587**. Source accounting
covers1,701base units;4,772base and six fine units remain unresolved.
All prior case bindings,2,013reviews,22links,R402andbaseline are preserved.
The172-method metadata selection passes. This source-only registration
adds no compiler invocation and preserves the actual contexts of batch067's
selected observations and batch059's full report.
See `doc/source_audits/batch_068.json`.

A further source-only packet covers 7.5.8 and 7.5.9 with 13 base units,
50 fine units, 14 requirements and 72 pending facets. It preserves existing
canonical witnesses and explicitly accounts for the value-set definition
without inventing a no-op execution. Its four-file author commit `1fada1e`
has passed independent source-eligibility review; no main-checkout coverage
was credited by the source-only packet. The 7.5.9 compile subset is now
integrated separately as batch020. The unchanged7.5.8source half is now
registered as batch052. Batch057 now represents its13value facets through
independently reviewed finite connections over five unchanged programs,
without a fabricated value-set classifier or duplicated execution.
Source-only constructor packet `8ba944c` in 7.5.10 covers 28 base and
114 fine units, with 22 requirements and 98 facets: two already represented
C7107 facets and 96 pending. The four existing C7107 programs and their
primary ownership remain; the new detailed metadata intentionally exposes
four stale case bindings and three stale links. Its independent source gate
has passed, not automatically renewed those receipts. Constructor packet
`9169f1c` now contains 28 new compile cases with 13 minimal repairs,
representing 20 new facets alongside the two existing C7107 facets and
retaining 76 pending. Independent fixture/cause review found no blockers:
all 17 valid controls compile with GNU, with 29 reference-eligible selections
and three source-only negatives among the 32 selected cases. Batch023
records their integration and the explicit four-case/three-link renewals.
All 76 remaining facets, including 48 facets of eight S-owned runtime
requirements, stay pending without source-use or runtime credit from these
compile controls.

The enum/enumeration source packet `fa1fbf02` also passed independent
eligibility review: 39 base units, 147 fine units, 28 requirements and
116 pending facets. Its two catalogues do not change any of the author's
1,849 case fingerprints or four links, but would stale the observational
inventory through its changed source context. That renewal remains explicit.
The conditional range of the note's12345 example, NEXT's endpoint error
termination, and outstanding companion/representation/BOZ qualifications
are preserved rather than turned into unqualified positive tests.
The unnamed-enum subset is integrated as batch022. Separate 7.6.2 packet
`90ae55e` is integrated in batch025 after independent source/oracle review:
three source-only run contracts, eight represented facets and 44 pending.
All nine original attempts and the three checkpoint target attempts stopped
at compilation. There is no successful native runtime, reference execution
or runtime sensitivity, and no INTEGER substitute.

BOZ source packet `c0c9e5de` passed independent review: ten base units,
83 fine units, nine requirements and 64 pending facets. It preserves exact
bit/context/consumer conditions, C7127 for typed REAL arrays, and the
distinction between STORAGE_SIZE's array-element quantity and physical
isolated-scalar width. Its source-only registration changes no case or link
fingerprint but stales the observational inventory through source context.
The real-BOZ representation bridge remains unresolved; this is not a
profile, fixture or oracle approval. Binary/octal packet `7634eddd` is now
integrated in batch025 for 12 compile facets, retaining 52 pending and the
separate real-BOZ block. Array-constructor source is integrated as batch024.
Its original value packet `5161d38e` remains unapproved historical evidence
after AVFR-001 identified invalid direct RANK constructor-expression
observers. Correction `583dcb6d` is integrated in batch028 after complete
independent review, with valid assumed-rank observers and unchanged literal
oracles. The old 35 probe runs do not qualify the corrected sources; three
current target scalar-CHARACTER probe gaps remain explicit.

Declaration packet `ad515fc`, C801 packet `0a7331bc` and corrections
`02633cd0`/`4fa94cdb` are integrated in batch030 after all three independent
closeouts. The 28 base and 116 fine units retain 23 requirements, six
represented facets and 118 pending facets. Earlier observations and retired
reviews remain historical, not relabelled. All later main cases and nine
links are preserved. Source-only 8.3/8.4 is integrated
as batch027; seven local type-parameter capture facets are integrated in
batch029, while initialization8.4 remains pending. C814 packet `1397017b`
and corrections `0fb7640e`/`aa7d8cc0` are integrated in batch034 after
independent predicate and test-ownership closeout. Its five facets have
ten compile cases; four other C814 facets remain pending. Source8.5.1/8.5.2 passed
independent review with six C815 metadata and six source-dependent link
staleness gates. C815 packet `61f4eaed` and correction `d1c3bf6b` are now
integrated as batch036 after both independent closeouts and explicit
source/case/six-link/inventory renewals. All49remaining packet facets stay
pending. ALLOCATABLE/ASYNCHRONOUS source `f20d7d53` is
integrated as batch031, with no fixture or source-use credit. BIND data
source `3a7df6a8` is integrated as batch032, also with no new cases.
CODIMENSION source `a2dd92aa` is integrated as batch035 with all80facets
pending. CONTIGUOUS source `542612ce` is integrated as batch038, with all36
facets pending. DIMENSION general/explicit-shape source `b3475d41` is
integrated as batch039, with all78 facets pending. Assumed/deferred-shape
source `b2df630` is integrated as batch041, with all49 facets and the
pointer-bound canonical-mechanism coverage gates pending. Assumed-size/
implied-shape source `b0f9d2b` is integrated as batch043 with all59 facets
pending. Assumed-rank source `7e010106` was integrated as batch047 with all32
facets pending; batch060 now represents two ordinary rank-effect facets,
without closing the other30. Coordinator-authored EXTERNAL/INTENT source packet
`da6cf5d` is registered as batch053 after independent source eligibility
review:23base/104fine units,21requirements and97pending facets. Nine
numbered units were already globally accounted; registration newly accounts
14base units, not23. It supplies no fixture or compiler observation.
INTRINSIC/OPTIONAL source packet `14c607c` is registered as batch054 after
independent source review: six base/24fine units, four requirements and
23pending facets, with no fixtures or compiler observations. PARAMETER and
POINTER source `010e6f5` is registered as batch058 after independent review,
with all38 facets pending. PROTECTED/SAVE source `bc5a85fc` is registered
as batch061 after independent review, with all90facets pending. STOP source
completion `00269110` is registered as batch062 with38new facets pending
and the original calibration unchanged. RANK/VOLATILE `deb25880` is
registered as batch063 with51facets pending. Correctly numbered TARGET/VALUE
in8.5.18/.19 are registered from `e2cef4b8` as batch064 with37facets pending. The intervening
8.5.17 is the RANK clause, not TARGET. Source eligibility is not fixture or
execution approval.

Bound-COMMON SAVE runtime authoring stopped before any fixture or compiler
run at BCS-ROLE-001: an explicit-SAVE confirmation needs a positive-control
role under an S-owned effect requirement. Separate opt-in per-facet role
support is now independently reviewed and integrated in batch042; the
actual BIND source opt-in and two complete programs are integrated in
batch046 after independent source/fixture/oracle review. Three S2 facets
remain pending, and the confirmation is not retagged as an effect.
Shared SHORT correction `0c7161ba` is integrated as batch040
after independent closeout. The original C830 candidate `ce23c2d` remains
immutable historical evidence; correction `0b62b0e` is integrated in batch045
after independent source, repair, cause/origin and native-evidence closeout.
Batch045's twelve compile cases represent seven facets. Batch048 supplies
disjoint-anchor infrastructure, and batch050 closes C830-ANCHOR-001 with the
original source-qualified assumed-size pair and explicit fourteen-case
adjudication. Fourteen compile cases now represent eight finite facets,
without source coalescing, a widened span or a false GNU conformance failure.
Batch056 adds two independently reviewed S1runtime-effect facets with
preserved target failures;26 other local S facets remain pending.

Source-use candidate `29fc461` and correction `b9150e82` are integrated as
batch026 after independent SULR-001 closeout. That infrastructure checkpoint
contained no actual inventory. The first finite R402 declaration-name census
is now independently reviewed and integrated as batch033. It distinguishes
assumed `function-name` from explicitly defined `object-name` in the
complete8.2 scope, while leaving the whole-standard target pending.
The broader meta-evidence contract, including mixed FORMAT
diagnostic contexts, is not complete merely because one link type exists.
Meta-level definitions must not become fabricated passing programs.
Continue to separate reporting, selected interfaces, finite controls, and
universal claims; all remaining source and evidence gaps stay explicit.
