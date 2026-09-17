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
The current census still has 4,886 unresolved base units and eight unresolved
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

A further source-only packet covers 7.5.8 and 7.5.9 with 13 base units,
50 fine units, 14 requirements and 72 pending facets. It preserves existing
canonical witnesses and explicitly accounts for the value-set definition
without inventing a no-op execution. Its four-file author commit `1fada1e`
has passed independent source-eligibility review; no main-checkout coverage
was credited by the source-only packet. The 7.5.9 compile subset is now
integrated separately as batch020; 7.5.8's 13 value facets remain pending
outside main, without a fabricated value-set classifier execution.
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
contains ten source-supported compile cases for five facets, but independent
review holds three negative oracles under ASFR-001: a short-format Internal
wrapper could be credited as the intended report. Separate predicate and
cross-owner pending-count test corrections are required; no current C814
facet is approved through that packet. Source8.5.1/8.5.2 passed
independent review with six C815 metadata and six source-dependent link
staleness gates. C815 packet `61f4eaed` has six migrations and five exact
second-statement deletion controls under independent review, without
renewing those records. ALLOCATABLE/ASYNCHRONOUS source `f20d7d53` is
integrated as batch031, with no fixture or source-use credit. BIND data
source `3a7df6a8` is integrated as batch032, also with no new cases.
The next bounded source packet covers CODIMENSION8.5.6.1-.3.

Source-use candidate `29fc461` and correction `b9150e82` are integrated as
batch026 after independent SULR-001 closeout. No actual use graph has been
completed by the empty registry.
One bounded R402 declaration-name census is being prepared outside main.
It distinguishes assumed `function-name` from explicitly defined
`object-name` in the complete8.2 source scope. Its source and inventory
approval remain separate gates; no census is yet credited or committed.
The broader meta-evidence contract, including mixed FORMAT
diagnostic contexts, is not complete merely because one link type exists.
Meta-level definitions must not become fabricated passing programs.
Continue to separate reporting, selected interfaces, finite controls, and
universal claims; all remaining source and evidence gaps stay explicit.
