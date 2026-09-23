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
The current census still has 4,688 unresolved base units and six unresolved
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

The sixty-ninth checkpoint registers independently reviewed CONTIGUOUS
statement source: two base/seven fine units, R839 and10pending facets.
Only p1 is newly accounted; R839 was already counted. Its actual
object-name-list uses explicit R804/C810, and C830 eligibility remains
separate from naming, actual contiguity or scalar effective rank.

There remain **2,049cases**, now with **121catalogues,702requirements,
1,756direct,22linked and1,819pending facets out of3,597**. Source accounting
covers1,702base units;4,771base and six fine units remain unresolved.
All case bindings,2,013reviews,22links,R402andbaseline are preserved.
The14C830 cases and two prior contiguity effects use type attributes, not
standalone statement occurrences; their failures, ICE and26UNTESTED plans
are not promoted or relabelled. The172-method metadata selection passes,
with no compiler invocation. See `doc/source_audits/batch_069.json`.

The seventieth checkpoint registers independently reviewed accessibility
statement source:10base/63fine units, eight requirements and42pending
facets. Four base units are newly accounted after six numbered units already
counted. List/default/module-policy and generic/name-space conditions stay
distinct from component, binding, implementation and constructor access.

New p1 accounting genuinely staled three existing binding connections.
Each received independent semantic eligibility, then an explicit
source-context renewal after source approval. Their specifications, roles
and two unique complete programs are unchanged; the other19link reviews
remain exact. **This adds no link, execution or passing linked aggregate.**
Old compiler observations retain their actual modes and contexts.

There remain **2,049cases**, now with **122catalogues,710requirements,
1,756direct,22current linked and1,861pending facets out of3,639**.
Source accounting covers1,706base units;4,767base and six fine units remain
unresolved. All case bindings,2,013case reviews,R402andbaseline survive.
The177-method metadata/link selection includes all32type-bound ownership
subsets and passes without compiler invocations.
See `doc/source_audits/batch_070.json`.

The seventy-first checkpoint registers the independently reviewed C877
empty/blank-NAME cardinality cases. Both invalid declarations are repaired
by deleting only the NAME clause and converge to **one shared compile
positive control**. GNUf2023corroborates all three expectations. The frozen
target and actualFlangf2018silently accept both invalids; those reporting
failures remain explicit rather than being normalized into allowed results.

There are now **2,052cases**, with **1,758direct,22linked and1,859pending
facets out of3,639**; source counts are unchanged. Only the two reviewed,
currently observed target failure IDs were added to the baseline, preserving
every old line, note and ordering. A separate normal selection reports
**one PASS and two XFAILs**, with one control compile per configuration and
no runtime effect. These remain target failures, not conformance passes.

All2,049prior case bindings,2,013raw reviews, the three batch070 link
renewals, all22current links and R402 remain unchanged. The41-method
focused selection passes. This is a selected three-case observation, not
a new full-suite report. See `doc/source_audits/batch_071.json`.

The seventy-second checkpoint adds four independently reviewed R839
standalone CONTIGUOUS cases, representing three facets. Each missing-list
form has a one-name-insertion compile control. Independent review corrected
an oracle that admitted only one compiler's wording: the exact expected-name
reports now qualify in both fixed contexts, and the exact premature-newline
report qualifies only after the double colon. Source, location, shielding
and native-failure safeguards remain unchanged. Generated prose no longer
reinstates historical verdicts after correction or approval.

The current target selection reports **three PASS and one XFAIL**. The
bare-form unsupported-attribute report remains a failure; it is not silent
acceptance. GNU actual f2023 passes all four expectations; Flang's four
passes remain supplementary f2018 evidence. Only the one approved current
target failure was added to the baseline. Original reports and all four
Fortran sources remain unchanged.

There are now **2,056cases**, with **1,761direct,22linked and1,856pending
facets out of3,639**. All2,052prior case bindings,2,016raw reviews,22links
and R402 survive. The45-method focused selection and current observations
retain their exact contexts; no new full-suite execution is claimed.
See `doc/source_audits/batch_072.json`.

The seventy-third checkpoint registers independently reviewed DATA statement
source:37base/184fine units,33requirements and185pending facets. Twenty-five
numbered units were already counted; the eleven paragraphs and complete note
newly account **12base units**, not37. Initialization, expanded sequence/count
rules, pointer/state/SAVE conditions and representation-dependent oracles
remain explicitly qualified. The failed broad annex read is not claimed
complete; the required dependencies were separately checked.

There remain **2,056cases**, now with **123catalogues,743requirements,
1,761direct,22linked and2,041pending facets out of3,824**. Source accounting
covers1,718base units;4,755base and six fine units remain unresolved.
All case bindings,2,020raw reviews,22links,R402andbaseline are unchanged.
The172-method metadata selection passes without compiler invocations;
batch072's actual four-case selection retains its122-catalogue context.
See `doc/source_audits/batch_073.json`.

The seventy-fourth checkpoint registers independently reviewed DIMENSION
and INTENT statement source: six base/34fine units, two syntax requirements
and23pending facets. Four base units are newly accounted. The explicit
DIMENSION repetition and zero-rank bounds-vector route stay distinct from
ordinary zero-extent arrays. INTENT uses explicit R1534 dummy names and
retains data/procedure-pointer eligibility and canonical IN/OUT state rules.

There remain **2,056cases**, now with **125catalogues,745requirements,
1,761direct,22linked and2,064pending facets out of3,847**. Source accounting
covers1,722base units;4,751base and six fine units remain unresolved.
All case/review/link/R402/baseline bindings survive. The172-method metadata
selection passes; no compiler, rank/state effect or numbered-wrapper
connection is added. See `doc/source_audits/batch_074.json`.

The seventy-fifth checkpoint registers independently reviewed OPTIONAL and
PARAMETER statement source:10base/49fine units, seven requirements and44
pending facets. Seven base units are newly accounted. OPTIONAL keeps its
actual dummy-name/role/presence owners. PARAMETER retains subsequent typing
under the real implicit mapping, prior rank, the two conditional shape
branches and independently justified constant-value/conversion oracles.
None of those planned effects is replaced by a compile-only classifier.

There remain **2,056cases**, now with **127catalogues,752requirements,
1,761direct,22linked and2,108pending facets out of3,891**. Source accounting
covers1,729base units;4,744base and six fine units remain unresolved.
All old cases,2,020reviews,22links,R402andbaseline are preserved. The172
metadata methods pass without compiler invocations; source/inventory
adjudication is not an execution or representation-profile approval.
See `doc/source_audits/batch_075.json`.

The seventy-sixth checkpoint registers independently reviewed POINTER and
PROTECTED statement source after PPSR-001 closeout. Correction `396598d`
changes exactly two C892 references and one generated line to the actual
dummy-procedure owner15.5.2.10, rather than the coarray owner15.5.2.9. The
initial blocked proposal and review remain immutable. Seven base/25fine
units contain four numbered requirements and33pending facets; three base
units are newly accounted. Actual EXTERNAL-conferring routes, data versus
procedure identity, canonical C855 reuse, protection scope and pointer
state/lifetime conditions remain explicit future fixture gates.

There remain **2,056cases**, now with **129catalogues,756requirements,
1,761direct,22linked and2,141pending facets out of3,924**. Source accounting
covers1,732base units;4,741base and six fine units remain unresolved.
All old case/review/link/R402/baseline bindings survive. The original
independent172-method review, narrow14-method closeout and current main
172-method selection retain their separate scopes. No compiler observation
or missing-EXTERNAL negative/control is supplied. Source registration is not
fixture approval. See `doc/source_audits/batch_076.json`.

The seventy-seventh checkpoint registers independently reviewed VALUE and
VOLATILE statement source: four base/14fine units, two syntax requirements
and23pending facets. Two base units are newly accounted. The independent
review reads20complete original sections and selected units of eight more,
verifies all28section hashes and202original units, and confirms explicit
R1534/R804 name ownership in the complete502-head grammar census.
Actual data-dummy roles, anonymous-object/component semantics, scoped
VOLATILE identity and the mandatory-versus-advisory boundaries stay exact.

There remain **2,056cases**, now with **131catalogues,758requirements,
1,761direct,22linked and2,164pending facets out of3,947**. Source accounting
covers1,734base units;4,739base and six fine units remain unresolved.
All old cases,2,020reviews,22links,R402andbaseline remain unchanged. The172
main metadata methods pass; no compiler, copying/ABI effect, timing oracle
or fixture approval is supplied. See `doc/source_audits/batch_077.json`.

The seventy-eighth checkpoint registers independently reviewed SAVE and
TARGET statement source:11base/46fine units, seven numbered requirements
and44pending facets. Four base units are newly accounted. SAVE's nested
optional list/colon group, same-scope C893 antecedent and actual procedure
pointer/COMMON roles remain distinct. TARGET's array/coarray declaration
groups retain category, scope and lifetime conditions rather than a
CONTIGUOUS-style name-only interpretation. Eight complete existing inputs
were checked for actual standalone occurrences without adding canonical
connections or changing their roles.

There remain **2,056cases**, now with **133catalogues,765requirements,
1,761direct,22linked and2,208pending facets out of3,991**. Source accounting
covers1,738base units;4,735base and six fine units remain unresolved.
All old case/review/link/R402/baseline bindings are preserved. Independent
and main172-method metadata selections pass without compiler invocations.
No SAVE retention, TARGET lifetime or new grammar observation is supplied.
See `doc/source_audits/batch_078.json`.

The seventy-ninth checkpoint integrates six independently reviewed PARAMETER
value-effect programs from `c4be9b2`. Actual named constants, not mutable
stand-ins, are observed against independent integer, logical, character and
array values. Full-program guard and omission review retains230sensitive
mutation runs and34target plans untested behind failed parents. Current main
reproduces four target passes, a CHARACTER-truncation runtime failure and a
scalar-array initialization internal compiler error. Only those two approved
failures enter the baseline after fresh reproduction; GNUf2023qualifies all
six effects, while Flangf2018success remains supplementary.

There are now **2,062cases,133catalogues,765requirements,1,767direct,
22linked and2,202pending facets out of3,991**. Source accounting remains
1,738/6,473base units. All2,056old case bindings,2,020old reviews,22links and
R402survive unchanged. Simple-derived and numeric-kind/BOZ gates remain
pending. The186main metadata methods pass. The current selected execution is
`batch079-selected-native.json`; last actual full execution and full Python
suite remain batch059's2,041cases and837methods, not current full runs.
See `doc/source_audits/batch_079.json`.

The eightieth checkpoint integrates three independently reviewed DATA
position/initial-state programs from `36e9f1b`: scalar correspondence,
rank-two array element order, and initialization despite physical placement
after RETURN. Actual DATA subjects have independent literal/coordinate
oracles; all mutations retain initialization, including defined-result
omission models. Independent review reproduces nine passing parents and
129sensitive mutations. Current main gives three target and three GNUf2023
qualified effect passes; three Flangf2018passes remain supplementary.
The actual GNU obsolescence warning is preserved without new reporting credit.

There are now **2,065cases,133catalogues,765requirements,1,770direct,
22linked and2,199pending facets out of3,991**. All2,062old case bindings,
2,026old reviews,22links,R402and the `b153c75b` baseline survive unchanged.
The other182DATA facets remain pending. The184main metadata methods pass,
and `batch080-selected-native.json` is the actual latest main selection in
its2,065-case context. Source accounting remains1,738/6,473; last actual full
execution/Python results remain the historical batch059 results.
See `doc/source_audits/batch_080.json`.

The eighty-first checkpoint registers independently reviewed IMPLICIT
source:18base/111fine units, nine numbered and two S requirements, and
59pending facets. Nine base units are newly accounted. The source review
reads275original units, verifies40section hashes and502grammar heads, and
visually checks statement ordering. NONE(), null versus EXTERNAL-only maps,
letter membership, actual scope/type/parameter identity and the explicit
interface-or-EXTERNAL duty retain their separate conditions and owners.

There remain **2,065cases**, now with **134catalogues,776requirements,
1,770direct,22linked and2,258pending facets out of4,050**. Source accounting
covers1,747base units;4,726base and six fine units remain unresolved.
All old cases,2,029reviews,22links,R402andbaseline are preserved. The172main
metadata methods pass; there is no new compiler observation or fixture
approval. The last actual selected execution remains batch080 in its
133-catalogue context. See `doc/source_audits/batch_081.json`.

The eighty-second checkpoint registers independently reviewed IMPORT
source:18base/71fine units, eight numbered and seven S requirements, and
79pending facets. Ten base units are newly accounted. Ordinary versus BLOCK
filters, five default scope categories, actual interface identity, statement
ordering, implicit mappings and named/ALL no-hiding conditions retain their
original limits. Basic named-list leads and real value/graph observers stay
pending. The independent review's corrected metadata guard did not change
the candidate or introduce compiler execution.

There remain **2,065cases**, now with **135catalogues,791requirements,
1,770direct,22linked and2,337pending facets out of4,129**. Source accounting
covers1,757base units;4,716base and six fine units remain unresolved.
All old case/review/link/R402/baseline bindings are preserved. The172main
metadata methods pass; no new native observation or fixture approval is
supplied. See `doc/source_audits/batch_082.json`.

The eighty-third checkpoint registers independently reviewed NAMELIST
source:11base/40fine units, five numbered and five S requirements, and
47pending facets. Six base units are newly accounted. The review verifies
470original units across53sections. Enumeration/direct-component restrictions,
whole-group transfer state and defined-I/O requirements remain distinct;
READ-back equality is not an oracle for output order or multiplicity.
All output-parser, full-I/O lifecycle and sensitivity plans stay pending.

There remain **2,065cases**, now with **136catalogues,801requirements,
1,770direct,22linked and2,384pending facets out of4,176**. Source accounting
covers1,763base units;4,710base and six fine units remain unresolved.
All old cases,2,029reviews,22links,R402andbaseline survive unchanged.
The172main metadata methods pass without compiler invocations. Last actual
main selection remains batch080 in its133-catalogue context; no source
registration is a new full-suite execution. See `doc/source_audits/batch_083.json`.

The eighty-fourth checkpoint registers independently reviewed COMMON and
related storage restrictions:29base/166fine units across six sections,
seven numbered and17S requirements, and117pending facets. Twenty-two base
units are newly accounted. Independent review checks726original units
across109sections,502grammar heads and the original Table9.1. Language
storage sequences, type/parameter identity, definedness, named/blank
differences, SAVE and initialization/lifetime conditions remain separate.
The block-size section is definition-only; three zero-payload association
facets are positive controls, not empty runtime effects.

There remain **2,065cases**, now with **142catalogues,825requirements,
1,770direct,22linked and2,501pending facets out of4,293**. Source accounting
covers1,785base units;4,688base and six fine units remain unresolved.
All old cases,2,029reviews,136oldercatalogues,22links,R402andbaseline are
preserved. The172main metadata methods pass; source registration and the
separate inventory renewal supply no new compiler observations.
See `doc/source_audits/batch_084.json`.

The eighty-fifth checkpoint registers the independently reviewed EQUIVALENCE
statement source:25base/129fine units across five sections,14numbered and
seven S requirements, and130pending facets. Eleven base units are newly
accounted, completing Clause8 source accounting through8.10.3. The review
verifies the five scoped sections and their25original units,13referenced
sections with79units, and502grammar heads. R873 has no double-colon form,
R874 requires at least two members, and R875 admits only variable names,
array elements and substrings. C8110 retains all eleven base-object
exclusions as alternatives; C8114-C8117 stay four separate family rules;
C8118 remains a condition on the program while8.10.1.2p2 confers SAVE on the
other set members with explicit confirmation merely permitted. Default
character association keeps its own first character storage unit, a nonzero
whole array name aligns with its first element under the actual declared
bounds, and the two unnumbered8.10.1.5 prohibitions stay distinct with a
context-dependent rather than numbered-constraint reporting duty.

The first review pass returned quickly and reported no blocking finding, so
the coordinator reproduced every mechanical accounting and identifier check,
re-read8.10.1.1-.5 and9.4.1 in the original, and required answers to three
targeted questions before recording any review. That follow-up confirmed the
conferred-versus-required SAVE and PROTECTED distinction, the unnumbered
prohibition scope, and retention of the19.5.3.4 default-initialization
cross-reference. The reviewer had not read9.4.1; the coordinator verified
that R908-R910 require an explicit substring range, so C8120's limitation to
substring occurrences is correct.

There remain **2,065cases**, now with **147catalogues,846requirements,
1,770direct,22linked and2,631pending facets out of4,423**. Source accounting
covers1,796base units;4,677base and six fine units remain unresolved.
All old cases,2,029reviews,142oldercatalogues,22links,R402andbaseline are
preserved, and the generated views regenerate byte-identically. The934-method
Python suite passes and no compiler was invoked. Source registration is not
fixture approval: every storage-association, alignment and storage-unit plan
remains a pending gate, and no byte layout, address arithmetic, TRANSFER
result or undefined-alias read is accepted as an oracle.
See `doc/source_audits/batch_085.json`.

The eighty-sixth checkpoint integrates four independently reviewed COMMON
ordered-list run/effect programs for S8.10.2.1-001: repeated `/packet/` groups
in one statement, successive named statements, the omitted-name plus `//`
spellings of the same blank block, and interleaved `/left_block/` and
`/right_block/` statements. Each represents exactly one facet;113 other
8.10.2.1 facets keep their original pending plans. A separately called and
counted seed defines every observed storage unit to a negative sentinel
before the writer, so neither the observations nor any mutation reads
undefined storage, and readers compare each actual COMMON coordinate against
independent literals rather than a commutative sum, an address or a TRANSFER
result. All four are reference-validated by GNU Fortran16.1.0 in f2023; the
frozen target and Flang's f2018 runs also pass, but neither adjudicates.
All507 whole-program wrong-oracle and omission mutations,169 per compiler,
failed at their predicted guards.

Independent fixture review raised and closed three blocking findings.
CLER-001: after the cases existed, the requirement's inherited oracle and
limitation text still said no such program or mutation had been implemented
and that no case was created, while the generated view rationalised keeping
that wording. CLER-002 and CLER-003 were successive weaknesses in the
coordinator's replacement guard, which first accepted mixed stale-plus-current
wording and then stale-plus-reworded near-variants. The final guard pins
distinctive content anchors to the exact corrected sentences and is exercised
by eight rejection vectors per protected field. No Fortran byte changed, but
the requirement-metadata correction staled the four case fingerprints, so both
native stages were re-run rather than reused; the pre-correction artifacts are
preserved separately.

There are now **2,069cases**, with **147catalogues,846requirements,
1,774direct,22linked and2,627pending facets out of4,423**. Source accounting
remains1,796/6,473base units. All2,065prior case bindings,2,029reviews,
22links, R402 and the `b153c75b` baseline are unchanged, and no baseline entry
is added. Declaration text is source-reviewed rather than mutation-probed,
f2018 success stays supplementary, and the retained needs-oracle real-BOZ case
still makes the normal whole-suite gate nonzero.
See `doc/source_audits/batch_086.json`.

The eighty-seventh checkpoint opens Clause 9 by registering the independently
reviewed Designator, Variable and Constant source:19base/44fine units across
three sections,14numbered and three S requirements, and50pending facets.
Five base units are newly accounted. The review reads the19original units,
18referenced sections and all502grammar heads. R901's seven designator
alternatives stay owned by9.4.x and9.5.x rather than being duplicated here.
C901 excludes a constant and any subobject of one, including a substring of a
literal constant through the R909 parent-string alternatives. C902 requires a
data pointer result and9.2p1 requires that pointer to be associated, while
R904-R907 share the general variable grammar and take their types from the
paired constraints. The definedness effects of9.2p2 carry no diagnostic duty,
because a reference to an undefined variable is generally not statically
detectable; their plans use positive controls with literal oracles, and no
plan executes an undefined read. The unnumbered note stays informative, and
9.3's never-permitted redefinition is owned as prose while diagnostics remain
with C901 and the assignment and definition-context owners.

A fresh-context author produced the packet in an isolated worktree and
declared four interpretation risks; a separate fresh-context reviewer answered
each and returned no blocking finding. The coordinator reproduced the
accounting and identifier checks, re-read9.1-9.3 and9.4.1 in the original, and
audited every definedness plan before recording any review.

There remain **2,069cases**, now with **150catalogues,863requirements,
1,774direct,22linked and2,677pending facets out of4,473**. Source accounting
covers1,801base units;4,672base and six fine units remain unresolved. All
2,069case bindings,2,033reviews,147oldercatalogues,22links,R402 and the
`b153c75b` baseline are preserved, the generated views regenerate
byte-identically, the948-method Python suite passes and no compiler was
invoked. Sections9.4 through9.7 are queued as eight further source packets and
remain unauthored.
See `doc/source_audits/batch_087.json`.

The eighty-eighth checkpoint registers the independently reviewed Substring
and Structure component source:32base/101fine units across two sections,
19numbered and eight S requirements, and115pending facets. Thirteen base
units are newly accounted. The reviewer read all32original units in full and
verified all502grammar heads. R908-R910 require an explicit substring-range,
so a whole scalar variable or array element is not a substring occurrence,
and C908 keeps the character-type condition on the parent string. The
starting and ending points, the MAX(l-f+1,0) length, the default endpoints of
one and n, the zero-length case when the starting point exceeds the ending
point and the otherwise-in-range requirement stay distinct, with runtime
valued endpoint conditions given no invented static diagnostic duty.

In9.4.2, C909 and C910 keep the derived-type and component-of-declared-type
conditions on all but the rightmost and leftmost part-names, C911 constrains
only an abstract rightmost part-name, and C912 requires a data-object
leftmost name. C913 retains the exact rank equation and C914 the
cosubscript/corank equality. C915 excludes C_PTR, C_FUNPTR and TEAM_TYPE only
when some part-ref carries an image selector, while C916 requires a
section-subscript-list only for an array part-name with an image selector.
C917 and C918 keep both the intrinsic-inquiry and type-parameter-inquiry
exceptions, and C919 keeps both the single-nonzero-rank rule and the
ALLOCATABLE/POINTER prohibition to its right. Array sections, subscripts and
image selectors remain owned by9.5.x and9.6, components by7.5.x, and all
four notes stay informative.

There remain **2,069cases**, now with **152catalogues,890requirements,
1,774direct,22linked and2,792pending facets out of4,588**. Source accounting
covers1,814base units;4,659base and six fine units remain unresolved. All
2,069case bindings,2,033reviews,150oldercatalogues,22links,R402 and the
`b153c75b` baseline are preserved, the948-method Python suite passes and no
compiler was invoked. Sections9.4.3 through9.7 remain queued and unauthored.
See `doc/source_audits/batch_088.json`.

The eighty-ninth checkpoint registers the independently reviewed coindexed
named object, complex part designator and type parameter inquiry source:
13base/42fine units across three sections, six numbered and four S
requirements, and47pending facets. Seven base units are newly accounted.
C921 keeps three separate conditions on the data-ref: exactly one part-ref,
an image-selector in that part-ref, and a part-name naming a scalar coarray.
R915 supplies exactly the `%RE` and `%IM` forms, C922 requires a complex
designator, and p1 fixes the designated part, the real result type and the
designator's kind and shape, which may be array or scalar. C923 binds the
type-param-name to the **declared** type of the designated object, while
9.4.5p2's prohibition on inquiring about a deferred parameter of an
unassociated pointer or unallocated allocatable depends on runtime status
and therefore carries no required static diagnostic duty; no plan executes
such an inquiry. NOTE 1's non-variable, primary-only and scalar statements
stay informative here rather than becoming locally owned requirements.

The coordinator read the scoped source independently while the author worked
and caught a defect in its own task instruction: 9.4.5's note2 is on PDF
page154, so a single-page range made the reader's census assertion fail.
Inventory page positions are section starts, not ranges. The author reran the
corrected command and the committed packet needed no change.

There remain **2,069cases**, now with **155catalogues,900requirements,
1,774direct,22linked and2,839pending facets out of4,635**. Source accounting
covers1,821base units;4,652base and six fine units remain unresolved. All
2,069case bindings,2,033reviews,152oldercatalogues,22links,R402 and the
`b153c75b` baseline are preserved, the948-method Python suite passes and no
compiler was invoked.
See `doc/source_audits/batch_089.json`.

The ninetieth checkpoint registers the independently reviewed and corrected
whole-array, array-element and array-section syntax source:25base/66fine
units across three sections,17numbered and six S requirements, and81pending
facets. Eight base units are newly accounted. 9.5.1 states only that no order
of reference is implied except where array element ordering is specified, and
9.5.2 keeps its four distinct statements, including the EQUIVALENCE exception
owned by8.10.1.4 and the assumed-size restriction to actual arguments that do
not require the shape. C924 requires every part-ref to have rank zero with a
subscript-list in the last, C925 keeps its exact disjunction including the
complex-part alternative, and R919-R925 keep subscript, multiple-subscript,
subscript-triplet, multiple-subscript-triplet, stride and vector-subscript as
separate forms with C927, C928 and C929 on their actual owners. C930 and C931
keep their distinct assumed-size last-dimension conditions, while9.5.3.1p2's
in-bounds requirement stays runtime valued with no invented static diagnostic
duty and no plan that executes an out-of-bounds subscript.

Independent review returned **blocked** with three pending-plan attribution
findings. C9AR-001: an R919 scalar-subscript negative used `a([1,2])`, which
is a legal vector-subscript excluded in that context by C924's rank-zero
requirement, not by R919. C9AR-002: an R920 plan demanded a missing-`@`
diagnostic, although without `@` a rank-one integer vector still parses as a
vector-subscript, so any failure belongs to the C913 or C925 rank owners.
C9AR-003: a C930 positive control offered `a(:,:)` for assumed-size `a(3,*)`,
a form that violates C930 itself. The author corrected exactly three plan
strings; the reviewer verified the closeout by diff, confirmed no other field
changed and found no new finding. The original proposal stays immutable.

There remain **2,069cases**, now with **158catalogues,923requirements,
1,774direct,22linked and2,920pending facets out of4,716**. Source accounting
covers1,829base units;4,644base and six fine units remain unresolved. All
2,069case bindings,2,033reviews,155oldercatalogues,22links,R402 and the
`b153c75b` baseline are preserved, the948-method Python suite passes and no
compiler was invoked. Sections9.5.3.2 through9.7 remain queued.
See `doc/source_audits/batch_090.json`.

The ninety-first checkpoint registers the independently reviewed array
section, element order and contiguity source:26base/58fine units across six
subclauses,19S requirements and79pending facets. All26base units are newly
accounted, because these subclauses contain no numbered items of their own.
The reviewer independently derived Table9.1's subscript order value, which is
one plus the sum over dimensions of (s_i − j_i) multiplied by the product of
the preceding dimension sizes, with d_i equal to MAX(k_i − j_i + 1,0). The
automatic extraction of the rank-15 row misplaces a multiplication sign and
emits a stray fragment; the catalogue records that ambiguity explicitly
rather than resolving it silently, and a later visual confirmation of that
row remains outstanding.

The authoring agent was killed by a transient network failure after writing
the packet but before committing or self-reviewing. The coordinator validated
the output mechanically, committed it verbatim and instructed the reviewer to
apply extra scepticism. Review then returned **blocked** twice. C9SR2-001
found that the `S9.5.4-001` positive control `(:,2,1:3)` violates the very
bullet it was meant to support, since a scalar subscript precedes the triplet.
C9SR2-002 found that the coordinator's own correction reintroduced the
attribution defect: on a rank-three array the retained negative `(2,1:3)`
supplies only two section-subscripts and is already invalid under 9.4.2 C913,
so it could not demonstrate the9.5.4 bullet it was filed under. The negatives
are now `(:,2,1:3)` and `(2,:,1:3)`, each a legal rank-three list. That the
second finding was raised against an integrator-authored correction is the
intended behaviour of an independent review, not an exception to it.

There remain **2,069cases**, now with **164catalogues,942requirements,
1,774direct,22linked and2,999pending facets out of4,795**. Source accounting
covers1,855base units;4,618base and six fine units remain unresolved. All
2,069case bindings,2,033reviews,158oldercatalogues,22links,R402 and the
`b153c75b` baseline are preserved, the948-method Python suite passes and no
compiler was invoked.
See `doc/source_audits/batch_091.json`.

The ninety-second checkpoint registers the independently reviewed image
selector source:15base/50fine units, seven numbered and ten S requirements,
and56pending facets. Eight base units are newly accounted, completing Clause9
source accounting through9.6. R926 supplies the bracketed image-selector form,
R927 the scalar integer cosubscript and R928 the NOTIFY, STAT, TEAM and
TEAM_NUMBER selector-spec forms. C932 forbids a repeated specifier, C933
restricts NOTIFY to a variable designator in an intrinsic assignment, C934
makes TEAM and TEAM_NUMBER mutually exclusive, and C935 forbids a coindexed
STAT variable. The cosubscript-count sentence of p2 is accounted as
structural because the registered9.4.2 C914 owns that numbered equality, while
the cobound range and the image-index calculation stay under S9.6-002, so no
normative content is lost. Runtime-valued image, team and cobound conditions
receive no invented static diagnostic duty, and several plans are explicitly
marked as needing the separately gated multi-image capability.

A first attempt at this packet was lost to the same transient network failure
that killed the batch091 author, producing nothing; the packet was authored
from scratch. The reviewer's one nonblocking observation, an imprecise
`9.7R946` dependency reference, was acted on before registration: asked to
check the whole file for that class of defect, the author corrected nine
references, including `9.7.4R946`, `10.2.1.3`, `16.9.156`, `16.9.207`,
`16.9.208` and `16.10.2.22`, each independently reconfirmed by the reviewer.

There remain **2,069cases**, now with **165catalogues,959requirements,
1,774direct,22linked and3,055pending facets out of4,851**. Source accounting
covers1,863base units;4,610base and six fine units remain unresolved. All
2,069case bindings,2,033reviews,164oldercatalogues,22links,R402 and the
`b153c75b` baseline are preserved, the948-method Python suite passes and no
compiler was invoked. Clause9's remaining allocation subclauses in9.7 are
queued as four further packets and remain unauthored.
See `doc/source_audits/batch_092.json`.

The ninety-third checkpoint registers the independently reviewed ALLOCATE
statement source, the largest single subclause in Clause9:41base/99fine
units,13syntax rules,20constraints, seven S requirements and119pending
facets. Eight base units are newly accounted; the33numbered units were
already globally counted. The reviewer checked every numbered item
individually. R929 keeps the optional `type-spec ::` and alloc-opt list, R930
the ERRMSG, MOLD, SOURCE and STAT forms, R933 both allocation alternatives
including the parenthesized bounds form and the coarray bracket, and
R940/R941 the coarray and coshape specs with their trailing asterisk. C936
restricts each allocate-object to a data pointer or allocatable variable,
C937 requires a type-spec or source-expr for a deferred, unlimited
polymorphic or abstract object, and the remaining constraints retain their
exact type, kind, length, rank, corank, SOURCE and MOLD conditions.

Review returned **blocked** with two findings, both closed and independently
verified. ASR-001: the C952 negative used a SOURCE= form whose program also
violates the separate p4 dynamic-type restriction, so it was invalid for two
reasons and could not isolate C952; it now uses MOLD=, whose source-expr
declared type C952 still governs while p4 does not apply. ASR-002: the
S9.7.1.1-004 plan lacked the multi-image coarray gating that its sibling
facets already carried. The sister packet's reviewer raised the same class of
gating omission as a nonblocking point, so both9.7 packets now state their
multi-image dependence consistently.

There remain **2,069cases**, now with **166catalogues,999requirements,
1,774direct,22linked and3,174pending facets out of4,970**. Source accounting
covers1,871base units. All2,069case bindings,2,033reviews,165older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, the
948-method Python suite passes and no compiler was invoked.
See `doc/source_audits/batch_093.json`.

The ninety-fourth checkpoint registers the independently reviewed allocation
semantics and NULLIFY source:26base/112fine units across9.7.1.2,9.7.1.3,
9.7.1.4 and9.7.2, three numbered and25S requirements, and93pending facets.
Twenty-three base units are newly accounted. These subclauses are dense effect
prose rather than grammar, so the reviewer compared them sentence by sentence.
The execution order and timing of bounds and cobounds evaluation, the SOURCE=
and MOLD= effects on value, type parameters and definition status, default
initialization on allocation, the resulting allocation status and shape, the
error path with STAT= and ERRMSG=, the pointer association status after
allocation of a target, and NULLIFY's disassociation with C956's condition are
all retained exactly. Processor-dependent outcomes stay recorded as processor
dependent rather than as mandated behaviour, no plan reads a MOLD-allocated
undefined value or deliberately triggers allocation failure, and an undefined
pointer status is not claimed to be directly observable.

The one nonblocking observation — a coarray mismatch plan that did not declare
its multi-image requirement — was closed before registration and the reviewer
independently rechecked every coarray and image-related plan across all four
catalogues. Since the sister9.7.1.1 packet was blocked for the same class of
omission as ASR-002, both9.7 packets now declare multi-image dependence
consistently.

There remain **2,069cases**, now with **170catalogues,1,027requirements,
1,774direct,22linked and3,267pending facets out of5,063**. Source accounting
covers1,894base units;4,579base and six fine units remain unresolved. All
2,069case bindings,2,033reviews,166oldercatalogues,22links,R402 and the
`b153c75b` baseline are preserved, the948-method Python suite passes and no
compiler was invoked. Clause9 now lacks only the9.7.3 deallocation subclauses
and9.7.4/9.7.5.
See `doc/source_audits/batch_094.json`.

The ninety-fifth checkpoint registers the independently reviewed deallocation
source:24base/70fine units across9.7.3.1,9.7.3.2 and9.7.3.3, three numbered
and23S requirements, and64pending facets. Twenty-one base units are newly
accounted. R944, R945 and C957 keep their exact forms and conditions; the
deterministic error condition for deallocating an unallocated allocatable, the
undefined pointer status caused by deallocating a TARGET allocatable, the
argument- and construct-association prohibitions, the procedure return, BLOCK
exit, function result, INTENT(OUT), intrinsic assignment and derived-type
component cases, finalization and the coarray conditions are all retained.

Review returned **blocked** with seven findings, all closed. Four were upheld:
the subclause title is "Form of the DEALLOCATE statement", a plan proposed
manufacturing a stopped or failed image, a facet was missing for9.7.3.2p10's
second trigger where the allocate-object merely has a coarray potential
subobject component, and the C descriptor dependencies omitted their Clause18
owners.

The other three exposed a defect in the coordinator's own author instruction.
It had forbidden any deliberately triggered deallocation error, but that rule
was aimed at resource exhaustion and fabricated failed images. 9.7.3.2p1 and
9.7.3.3p1 specify **deterministic** error conditions, and a program that
triggers one with a STAT= specifier is conforming, with 9.7.4p5 and p6
supplying a portable oracle. The rule was therefore narrowed rather than
applied to delete correct plans: a plan may exercise a deterministic
standard-specified error condition provided its oracle asserts only portable
properties, never a specific processor-dependent value. The reviewer
explicitly accepted that adjudication with its own source anchors. The same
reasoning was applied to the sister9.7.4/9.7.5 packet, where the reviewer then
correctly rejected a proposed ERRMSG oracle: because p2 leaves the message
content unspecified, even inequality with a chosen sentinel cannot prove the
assignment, so that branch stays classification-only while the portable
success branch survives as a real plan.

There remain **2,069cases**, now with **173catalogues,1,053requirements,
1,774direct,22linked and3,331pending facets out of5,127**. Source accounting
covers1,915base units. All2,069case bindings,2,033reviews,170older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, the
948-method Python suite passes and no compiler was invoked.
See `doc/source_audits/batch_095.json`.

The ninety-sixth checkpoint registers the independently reviewed STAT= and
ERRMSG= specifier source:10base/43fine units, one numbered and six S
requirements, and44pending facets. Nine base units are newly accounted, and
this **completes Clause9 source accounting**: all28Clause9 catalogues, from
9.1 through9.7.5, are now reviewed. R946's scalar integer stat-variable
satisfies the citations already made by the registered9.6,9.7.1.1,9.7.1.2 and
9.7.2 catalogues. Paragraph p1 is a recommendation because the source says
"should", and p2 is structural because it only scopes the rest of the
subclause; the reviewer accepted both dispositions independently. Paragraph p5
keeps the ordered stopped-image, failed-image and other-error values with
their exact owners16.10.2.28 and16.10.2.31, and p6 keeps the three per-object
status guarantees.

Five findings were closed across three rounds. Three were narrowed under the
same adjudication as the deallocation packet. One corrected imprecise
ISO_FORTRAN_ENV references. The fifth, **SER-005, was raised against the
coordinator's own directed revision**: having been told to assert that the
errmsg-variable changed from a preset sentinel, the reviewer objected that
9.7.5p2 leaves the message content entirely unspecified, so nothing guarantees
the assigned message differs from that sentinel and the oracle was unsound.
That is correct and was accepted without reservation. The two directions of p2
are not symmetric, so they are now split: the error branch is
classification-only and records that no value comparison can portably prove
the assignment, while the success branch remains a real plan, since p2 does
guarantee the value is unchanged when no error occurs. This is the boundary of
the narrowed error-oracle rule: exercising a deterministic error condition is
permitted, but only where the standard actually specifies something portable
to observe.

There remain **2,069cases**, now with **175catalogues,1,060requirements,
1,774direct,22linked and3,375pending facets out of5,171**. Source accounting
covers1,924base units;4,549base and six fine units remain unresolved. All
2,069case bindings,2,033reviews,173oldercatalogues,22links,R402 and the
`b153c75b` baseline are preserved, the948-method Python suite passes and no
compiler was invoked.

Clause9 completion is **source accounting only**. Every one of its698pending
facets is still without a fixture, no Clause9 requirement has an executed
case, and the whole-standard census remains unratified.
See `doc/source_audits/batch_096.json`.

The ninety-seventh checkpoint is the **first executable batch since the COMMON
ordered-list effects**, and the first fixtures anywhere in Clause9. Six
complete run/effect programs represent six of the seven S9.4.4-001 facets:
real-part selection, imaginary-part selection, kind inheritance, scalar shape,
array shape and the defining context. Only `result-real-type` stays pending,
because it needs a diagnostic control, and the eight R915 and C922 facets keep
their original plans.

The oracles are deliberately not uniform. The four value facets compare the
selected part against independent literals written in the program, never
against `REAL`, `AIMAG` or `CMPLX`, since comparing a designator with an
intrinsic would test the intrinsic rather than establish the designator's
effect. Real and imaginary parts are always distinct, so a wrong selection
fails, and every literal is an exactly representable dyadic value compared
exactly rather than with a tolerance. The kind facet uses no literal at all:
it compares `KIND(z%RE)` and `KIND(z%IM)` with `KIND(z)`, so no particular
numeric kind value is assumed. The array facet adds `SIZE` and an
independently computed `SUM`.

All six pass on the frozen target, GNU Fortran16.1.0 in f2023 and Flang in
f2018, and all123 wrong-oracle and omission mutations failed at their
predicted guards across the three compilers. GNU f2023 supplies the
qualifying reference; no baseline entry is added because the target passes.

Both blocking findings were raised against **integrator-owned text, not the
author's work**. CPFR-001 found that the stored catalogue review rationale
still asserted that all fifteen 9.4.4 facets were pending and that no case or
execution existed. CPFR-002 then found that the integrator's own replacement
overclaimed that every program compares against independent literals, which is
false for the kind facet. Both were corrected by re-recording the catalogue
review with per-facet accuracy. The content-bound review machinery had already
computed the catalogue state as stale, so the false text could not have passed
the audit silently, but it still had to be replaced rather than assumed. The
reviewer also recorded, and the integrator accepted, that the scalar-shape
facet is an adequate but limited scalar-context value witness rather than an
independent runtime rank inquiry.

There are now **2,075cases**, with **175catalogues,1,060requirements,
1,780direct,22linked and3,369pending facets out of5,171**. All2,069prior
case bindings,2,033reviews,22links,R402 and the `b153c75b` baseline are
unchanged, and the954-method Python suite passes.
See `doc/source_audits/batch_097.json`.

The ninety-eighth checkpoint **opens Clause10** with the expression grammar:
50base/131fine units across10.1.1 and10.1.2.1-10.1.2.9,43requirements and
187pending facets. Twenty base units are newly accounted; the30numbered units
were already globally counted.

The reviewer derived the precedence chain independently from the grammar
rather than accepting the author's summary, and found that summary matched
only coarsely. The catalogue now states the finer chain: primary, defined
unary, `**`, `* /`, unary `+ -`, binary `+ -`, `//`, one relation, `.NOT.`,
`.AND.`, `.OR.`, `.EQV.`/`.NEQV.`, and defined binary operators lowest. A
layer confusion here would have silently corrupted every later expression
requirement.

Five blocking findings were closed over three rounds, and they are
instructive. Three concerned oracles that **cannot work**: a literal value
cannot reveal the grouping of an associative operation such as `//` or
`.EQV.`, and an execution-path oracle cannot reveal `.AND.` grouping because
the standard does not require short-circuit evaluation, so a processor may
evaluate either operand or neither. One moved a defined-binary rejection off
R1023's *form* to the applicability and generic-resolution owners10.1.6 and
15.4.3.4.2.

The fifth was raised against the corrected text itself and is the sharpest.
The replacement wording had declared those groupings simply unobservable, but
that is true only for **intrinsic** operands. The same operator symbols can be
extended by defined operations, and a non-associative defined extension makes
the grouping observable by ordinary value comparison. Each affected plan now
scopes the limitation to intrinsic operands and records the defined-extension
route as its concrete future shape. A convenient unobservability claim is
itself a defect when it is too broad.

There remain **2,075cases**, now with **185catalogues,1,103requirements,
1,780direct,22linked and3,556pending facets out of5,358**. Source accounting
covers1,944base units;4,529base and six fine units remain unresolved. All
2,075case bindings,2,039reviews,175oldercatalogues,22links,R402 and the
`b153c75b` baseline are preserved, the954-method Python suite passes and no
compiler was invoked. Clause10 is only opened: 10.1.3 onwards and most of10.2
remain unauthored.
See `doc/source_audits/batch_098.json`.

The ninety-ninth checkpoint adds eight substring run/effect programs and
**completes S9.4.1-001**: contiguous portion, the starting and ending point
expressions, inclusive selection, both defaults, the `MAX(l-f+1,0)` length
formula and the zero-length case. The28 remaining9.4.1 facets under R908,
R909, R910, C908 and S9.4.1-002 keep their original pending plans.

This section has a specific trap, and the review was aimed squarely at it.
Fortran blank-pads the shorter operand in a character comparison, so a
comparison against a literal of the wrong length can succeed for the wrong
reason and hide exactly the off-by-one endpoint the facet is meant to catch.
The reviewer checked every comparison individually and confirmed that all
nonzero comparisons use equal-length operands. The only padding-weak
comparisons are the two against an empty literal, and in both cases the facet
is carried by an explicit `LEN` assertion rather than by that comparison.
Parents use all-different characters so an off-by-one changes the value, the
default facets compare the defaulted form against its explicit equivalent
rather than merely against a literal, the endpoint facets use integer
variables assigned by executed statements, and no character intrinsic such as
`INDEX` or `TRIM` is used as an oracle.

All eight pass on the frozen target, GNU f2023 and Flang f2018, and all246
mutations failed at their predicted guards with no vacuous mutation found. GNU
f2023 is the qualifying reference; no baseline entry is added. There were no
blocking findings.

There are now **2,083cases**, with **185catalogues,1,103requirements,
1,788direct,22linked and3,548pending facets out of5,358**. All2,075prior
case bindings,2,039reviews,22links,R402 and the `b153c75b` baseline are
unchanged, and the960-method Python suite passes.
See `doc/source_audits/batch_099.json`.

The hundredth checkpoint registers the independently reviewed precedence,
evaluation and intrinsic-classification source:27base/81fine units across
10.1.3,10.1.4 and10.1.5.1,17S requirements and91pending facets. All27base
units are newly accounted, because no numbered item falls in this scope.

This is where the standard's **processor latitude** lives, and it is the most
dangerous area in the project for inventing false oracles. A permission
wrongly promoted to a requirement, or a plan inferring behaviour from
evaluation order, would corrupt every later expression fixture. The reviewer
therefore enumerated the evaluation freedoms independently before comparing
them with the catalogue. The IF/WHERE/FORALL side-effect permission and the
permission for pure elemental operations to be performed in any order or
simultaneously are both recorded as permissions rather than requirements; the
conditional skipped-evaluation effect carries no side-effect oracle; and the
freedoms owned by10.1.7,10.1.8 and10.1.6.3 are recorded as oracle boundaries
and dependencies rather than as locally owned requirements.

No plan infers anything from which operand was evaluated or in what order,
asserts a result that a mathematically equivalent rewrite could change, or
uses a floating-point tolerance as an escape hatch, and the grouping of an
associative intrinsic operation is not claimed to be value-observable. Table
10.2 was checked against the table itself rather than the candidate's summary,
since automatic extraction interleaves its columns; the enumeration-type and
character-kind distinctions are preserved. There were no blocking findings.

There remain **2,083cases**, now with **188catalogues,1,120requirements,
1,788direct,22linked and3,639pending facets out of5,449**. Source accounting
covers1,971base units. All2,083case bindings,2,047reviews,185older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked. Clause10 remains partially registered:10.1.5.2 onwards
and most of10.2 are unauthored.
See `doc/source_audits/batch_100.json`.

The hundred-and-first checkpoint registers the independently reviewed numeric
and character intrinsic operation source:24base/42fine units across
10.1.5.2.1,10.1.5.2.2,10.1.5.2.3,10.1.5.2.4,10.1.5.3.1 and10.1.5.3.2,12S
requirements and45pending facets. All24base units are newly accounted,
because no numbered item falls in this scope; Tables10.3 and10.4 are base
units in their own right and are accounted as such.

This is the first scope where the standard states **arithmetic semantics that
look directly testable** — integer division truncates toward zero, complex
exponentiation yields the principal value, concatenation appends on the right
and its length is the sum — and the temptation is to turn each of them
straight into a value oracle. Three separate hedges forbid that.7.4.3 makes
real and complex values *approximations* to mathematical values;10.1.5.2.4p2
permits the processor to evaluate any mathematically equivalent alternative,
and p3 says outright that the computational results may differ; and10.1.9.3p4
leaves the result kind processor dependent wherever two operand kinds have
equal decimal range or equal decimal precision. So no nontrivial complex-power
component value, no reassociation-sensitive floating value, and no equal-range
or equal-precision mixed-kind result kind may become an oracle. Tolerance
comparison and reference-compiler agreement are explicitly not substitutes.

What survives is genuinely portable and is what the facets target: the
integer-division rule, which fixes the result exactly for exact small
operands; the same-kind concatenation value and its length-sum; and the
invariance of a parenthesized character value.

**10.1.5.3.2 yields zero facets.** That is a deliberate, reviewed conclusion,
not an omission: its single paragraph permits a processor to evaluate more of
a character intrinsic operation than the context requires, so no conforming
program may count function calls or observe skipped evaluation. The paragraph
and both its fine units are still accounted, as a permission. Likewise
10.1.5.2.1p4 (the processor need not convert an integer exponent) and
10.1.5.2.4p2 are permissions, and their parenthesis-integrity and
mathematical-equivalence limits are recorded as *boundaries* of those
permissions rather than as effects. Nothing in the packet asserts that a
processor did or did not take a rewrite — that is unobservable by design.
The reviewer read all24base units in the pinned document plus fourteen
dependency units in clauses7,10,15 and16, checked Tables10.3 and10.4 row by
row against the tables themselves, and confirmed that the NOTE2 alternative-
form table stays informative rather than being promoted to requirements.
There were no blocking findings; two non-blocking scope clarifications are
recorded as C10NR-NB1 and C10NR-NB2.

There remain **2,083cases**, now with **194catalogues,1,132requirements,
1,788direct,22linked and3,684pending facets out of5,494**. Source accounting
covers1,995base units. All2,083case bindings,2,047reviews,188older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked. Clause10 remains partially registered at this batch:
10.1.5.4 onwards and all of10.2 are unauthored.
See `doc/source_audits/batch_101.json`.

The hundred-and-second checkpoint registers the independently reviewed logical
and relational intrinsic operation source:24base/70fine units across
10.1.5.4.1,10.1.5.4.2,10.1.5.5.1 and10.1.5.5.2,19S requirements and68pending
facets. All24base units are newly accounted; Tables10.5,10.6 and10.7 are base
units in their own right.

This packet was **blocked on its first pass** with three findings, all closed
by a correction commit and then independently re-verified against the pinned
document. Two of them are the same defect twice.10.1.5.4.2p1 and10.1.5.5.2p1
each say that once the interpretation of an operation is established, the
processor *may* evaluate any other expression that is logically — or
relationally — equivalent, provided the integrity of parentheses is not
violated. Both had been catalogued as **effect requirements**. That is exactly
the error this project has ruled against before: processor latitude is a
`permission`, never a requirement, and never gets a plan asserting the
processor took it. Both were reclassified, and each of those two subclauses
now yields **zero facets** — the parenthesis-integrity limit and the NaN limit
survive as *boundaries* of the permission rather than as effects. A plan that
tried to detect whether a rewrite happened would itself be a defect.

The third finding is a plain source error. The relational oracle guidance had
been repeated across fourteen places telling a future author to use "exact
small integer, **logical**, enumeration, enum, and same-kind character
literals". But two operands of type logical cannot be compared with a
relational operator at all:10.1.5.5.1NOTE1 says so and Table10.2 does not
admit them. A logical-operand relational positive control would not even be a
conforming program. All fourteen occurrences were corrected and the count
independently confirmed.

Tables10.5,10.6 and10.7 were each checked row by row against the tables
themselves. Table10.6's four truth rows legitimately cover five operator
requirements, because `.NOT.` depends only on x2, so the apparently duplicated
x1 cases are genuine rows rather than missing ones. In Table10.7 the `< =` and
`> =` strings produced by text extraction are **artefacts**, not alternative
spellings; visual layout extraction of the original page confirms `<=` and
`>=`, and token ownership correctly stays with R1014 in10.1.2.7 rather than
minting spaced-token operator requirements.

Two attributions were checked substantively rather than taken on trust.
Character collation is owned by7.4.4.4, with term3.27 as terminology and the
LGT/LGE/LLE/LLT intrinsics in16.9.124-16.9.127 as a dependency boundary rather
than a substitute owner; blank padding of the shorter operand is stated
explicitly, limited for nondefault kinds by NOTE2. And10.1.5.5.1p6 owns the
rule that relational operands are converted to the type and kind of x1+x2,
while *determining* that type and kind is delegated to10.1.9.3p4 — a
delegation, not a duplicate requirement. The logical catalogues continue to
forbid side-effect, call-count, execution-path and skipped-operand oracles for
`.AND.` and `.OR.`.

Because batch101 and batch102 were authored in parallel from the same base,
both appended to `doc/catalogues/index.json`; the conflict was resolved by
keeping both appends in registration order, and all eight of batch102's files
were verified byte-identical to the reviewed corrected branch before any
review was recorded.

There remain **2,083cases**, now with **198catalogues,1,151requirements,
1,788direct,22linked and3,752pending facets out of5,562**. Source accounting
covers2,019base units. All2,083case bindings,2,047reviews,194older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked.
See `doc/source_audits/batch_102.json`.

The hundred-and-third checkpoint registers the independently reviewed defined
operation, operand evaluation and parenthesis source:20base/56fine units
across10.1.6.1,10.1.6.2,10.1.6.3,10.1.7 and10.1.8,10S requirements and
63pending facets. All20base units are newly accounted. Nine requirements are
effects and exactly one —10.1.7p3 — is a restriction.

This packet matters out of proportion to its size, because it is where **four
delegations left open by earlier Clause10 batches are finally discharged**.
Back in batch098 the reviewer refused to let the suite claim that the grouping
of a left-recursive *intrinsic* operation is value-observable: `//` is
associative by value, `.AND.` and `.EQV.` have no short-circuit guarantee, and
inferring grouping from a side effect or an execution path is not permitted.
The question was deferred to a **non-associative defined extension** — and
10.1.6 is where that extension becomes available. The packet supplies a
concrete plan: a derived type whose defining function returns
`left%v*10 + right%v`, with operands1,2 and3, which distinguishes
`(a//b)//c` =123 from `a//(b//c)` =33. The same route carries the `.AND.` and
`.EQV.`/`.NEQV.` grouping facets. The fourth delegation, from10.1.2.9, moves
defined-binary applicability and generic nonapplicability out of R1023 syntax
into10.1.6 and15.4.3.4.2 — with R1023, R1024 and C1006 syntax staying where
they are, and with no syntax negative filed for mere generic nonapplicability.

Every processor freedom in scope is a permission.10.1.6.3p1 lets the processor
evaluate any equivalent expression once the interpretation is established, but
only without violating the integrity of parentheses.10.1.7p1 says it is not
necessary to evaluate all of the operands, or to evaluate each entirely, if
the value can be determined otherwise — latitude, not a short-circuit
guarantee, and no plan infers whether an operand was evaluated. And10.1.8p1
was correctly **split**: the rewrite-latitude context inherited from10.1.5
stays a permission, while its counterweight — that any expression in
parentheses *shall* be treated as a data entity — stays a requirement. Neither
half was allowed to swallow the other. What parentheses do is force the
parenthesized expression to be the data entity operand of the surrounding
operation; what they do **not** do is create a portable observation of
evaluation order, call count, short-circuiting or floating-point reassociation.

The reviewer also ran a global name-head check over502rule heads —0missing,
0duplicate,0unmatched — confirming that the defined-operator grammar owners
remain R1004/C1005, R1024/C1006, R1012, R1020 and R1022 rather than migrating
into this scope. Two limits are recorded explicitly: the undefined-status
effect in10.1.7p2 is not safely value-observable by reading the entity, and a
finite sample can **refute** but never **prove** the all-possible-primary-values
equivalence condition of10.1.6.3p2. There were no blocking findings; three
non-blocking observations are recorded, one of which corrects a transcription
slip in the author's own accounting delta.

With this batch,10.1 is source-complete from10.1.1 through10.1.8.

There remain **2,083cases**, now with **203catalogues,1,161requirements,
1,788direct,22linked and3,815pending facets out of5,625**. Source accounting
covers2,039base units. All2,083case bindings,2,047reviews,198older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked. Discharging a delegation means a writable plan now
exists — not that a program has been written or run.
See `doc/source_audits/batch_103.json`.

The hundred-and-fourth checkpoint registers the independently reviewed
expression, primary and operation-result characteristics source:18base/49fine
units across10.1.9.1,10.1.9.2 and10.1.9.3,24requirements and81pending facets.

The central number in this batch is **10, not18**. Eight of the base units in
scope — R1025, C1007, R1026, C1008, R1027, C1009, R1028 and C1010 — were
already accounted by the numbered-rule inventory before this packet, so only
ten base units are newly accounted. They now additionally carry catalogue
records while still counting as one accounted base unit each. The reviewer
verified all eight individually and confirmed that none is double-counted and
none is dropped; a wrong number here would corrupt the whole-standard census.

10.1.9.3 is the interesting part, because it states result type, kind, length
and shape rules that *look* like exact oracles and in several cases are
deliberately underdetermined. The reviewer derived the rules independently
from the source before comparing them with the catalogue. Integer combined
with real or complex uses the real or complex operand kind. Different-range
integer pairs require the **greater** RANGE kind, and different-precision real
or complex pairs the **greater** PRECISION kind. But equal-range integer
pairs, equal-precision real or complex pairs, and different-kind logical
results require only that the result kind be **one of the operand kinds** —
which one is processor dependent. All three are recorded as permissions, and
the retained requirement is the weak property the standard actually states.
The fourth permission is the10.1.9.2p3 phrase admitting a disassociated
pointer only in contexts explicitly permitted elsewhere, which is a boundary
rather than a behaviour. The reviewer checked both failure directions and
found no other latitude needing a permission, and no genuine requirement
demoted into an untestable processor-choice oracle.

No plan hard-codes a kind value, predicts which operand kind is selected, or
assumes that multiple nondefault kinds exist; plans compare KIND, LEN, RANGE
and PRECISION against declarations, operands, `KIND(.TRUE.)` or dynamically
discovered supported kinds, and the greater-RANGE and greater-PRECISION plans
are conditional on that discovery.

Vacuity was checked explicitly, because this scope invites it. LEN is asserted
directly for character length. Disassociated pointers and unallocated
allocatables are given no SHAPE oracle. And the binary-operation shape plan
carries its own warning that two *conformable* arrays cannot discriminate the
x1-shape rule at all — conformability makes their shapes equal — so array-
scalar cases are offered instead. No table is a base unit in this scope;
Table10.2 is cited as a dependency and remains owned by10.1.5.1.

There were no blocking findings; two non-blocking observations record traps
for the future fixture work.

There remain **2,083cases**, now with **206catalogues,1,185requirements,
1,788direct,22linked and3,896pending facets out of5,706**. Source accounting
covers2,049base units. All2,083case bindings,2,047reviews,203older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked.
See `doc/source_audits/batch_104.json`.

The hundred-and-fifth checkpoint registers the independently reviewed
conformability, specification expression and constant expression source:
25base/105fine units across10.1.10,10.1.11 and10.1.12,20requirements and
117pending facets. Eight numbered units — R1029, C1011, R1030, C1012, R1031,
C1013, R1032 and C1014 — were already accounted, so17base units are newly
accounted, and those eight are used directly as requirement identifiers.

This is the first **constraint-dense** scope in Clause10, and that changes the
shape of the work. Almost all of its content is admission rules, so almost all
of its plans are negatives — and a negative filed against the wrong unit
establishes nothing at all. It took **three review rounds** to get right.

The first round confirmed two things and rejected a third. The +17 accounting
was verified unit by unit. The **zero-permissions** verdict was independently
adjudicated and accepted: every "may" and "permitted only if" in this scope —
including the TRANSFER text — conditionally admits a *program* construct
rather than granting the *processor* latitude. Zero permissions is unusual for
Clause10 but correct for a constraint-dense subclause. What failed was
C10CSR-001: a diagnostic/control pair filed against10.1.10p1, which says *"An
elemental operation is an intrinsic operation or a defined operation for which
the function is elemental"*. That defines and classifies; it prohibits
nothing. And if the non-ELEMENTAL function accepts array dummy arguments, the
operation is a perfectly valid *non-elemental defined operation* — so the
planned negative was not attributable to the rule it was filed under.
C10CSR-002 was smaller: p2 item (2) reaches directly into the OPTIONAL and
INTENT(OUT) attributes, but their owners were never recorded as dependencies.

The second round is the interesting one. Closing a finding does not close its
*class*, and the closeout found **C10CSR-003 — the same defect again**, at
10.1.11p4, which defines the term "specification function". A program using a
non-qualifying function in a specification expression is invalid through C1011
and p2, because the expression is then not a restricted expression; the
definition merely feeds that determination. Saying so in the facet text does
not repair filing the negative under the definition.

So the third round demanded a full sweep under an explicit rule, now a
project-wide precedent:

> A facet may carry a diagnostic expectation only if the source unit it is
> filed under **actually prohibits something** — an explicit `shall`,
> `shall not`, or a numbered constraint. A unit that defines a term,
> classifies a construct, or states what something *is* cannot support a
> negative, however obviously the definition feeds a nearby prohibition.

The sweep found a **fourth** instance, at p9, which the author fixed
themselves, and produced a38-row table naming, for every remaining diagnostic
plan, the exact prohibiting words in its unit and the single property
distinguishing the invalid program from its control. The reviewer did not
accept the table: they spot-checked twelve representative and high-risk row
groups against the pinned document — the whole C1012 p1 family, the C1011
ordinary-variable, OPTIONAL and INTENT(OUT) exclusions, the S10.1.11-004
direct-versus-indirect invocation pair the author had themselves flagged as
risky, the p6/p7/p8 ordering rows, C1013, C1014 and the10.1.12 p2 and p3 rows
— and found all of them sound.

One limitation deserves naming: three dummy-argument and procedure-reference
owners —15.5.2.1,15.5.2.4 and15.5.2.13 — are recorded as dependencies but are
**not yet registered**, so the C1011 exclusion negatives cannot be implemented
until they are.

There remain **2,083cases**, now with **209catalogues,1,205requirements,
1,788direct,22linked and4,013pending facets out of5,823**. Source accounting
covers2,066base units. All2,083case bindings,2,047reviews,206older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked. The38-row sweep table describes programs that *could* be
written; none has been written or run.
See `doc/source_audits/batch_105.json`.

The hundred-and-sixth checkpoint registers the independently reviewed
assignment statement source:14base/52fine units across10.2.1.1,10.2.1.2,
10.2.1.4 and10.2.1.5,21requirements and89pending facets. R1033 and C1015
were already accounted, so12base units are newly accounted. Table10.8 is a
base unit in its own right.

The interesting feature of this packet is its shape: **10.2.1.3 was already
registered, and it sits in the middle of the scope.** It owns26base units and
144facets. So the central question was not whether the source was read
correctly but where the boundary falls — and the failure modes are symmetric.
Claiming an effect10.2.1.3 already owns would duplicate a requirement;
punting a rule these sections genuinely own would leave a gap. The reviewer
read the existing catalogue in full and checked both directions.

There is no duplication. The10.2.1.2p1 allocatable, character-kind and
deferred-length plans **admit** those cases but leave the resulting
allocation, length, bounds, truncation, padding, conversion and values to
10.2.1.3. The p3 pointer plans require an associated definable conforming
target but leave the target write to10.2.1.3 and pointer association changes
to10.2.2.10.2.1.4 classifies the subroutine, generic, rank and shape
conditions and leaves element-by-element interpretation to10.2.1.5 and generic
mechanics to15.4.3.4.3. And there is no gap:10.2.1.1p1 owns the partition
rule rather than punting it, and10.2.1.2 keeps every local eligibility
condition — intrinsic-not-defined classification, polymorphic restrictions,
conformance and rank admission, BOZ destination type, Table10.8, character
kind compatibility, derived type parameter compatibility, coindexed
restrictions, pointer target eligibility, and the coarray or coindexed
unallocated-allocatable prohibition.

The zero-permissions verdict here is subtler than in batch105, and worth
recording. Assignment *does* carry processor latitude — but the sentence
permitting pure elemental subroutine assignments to be performed
simultaneously or in any order occurs **only in the unnumbered NOTE** in
10.2.1.5, which is informative. Meanwhile10.2.1.3, out of scope, contains
genuine normative latitude at p4, p7 and p16, already recorded as permissions
in its own catalogue. The contrast is what makes the verdict credible: the
distinction was drawn deliberately, not missed. Every plan here forbids order,
simultaneity, temporary, side-effect and call-count oracles.

Table10.8 was read row by row from the table itself, since extraction
interleaves its columns. All eight rows are owned. The enum row is the one to
watch, and it survives intact: when *expr* is integer, a primary in *expr*
shall be an enumerator of the enum type — **not** an arbitrary integer.
Conversion is left to10.2.1.3p13.

Character plans avoid the standing vacuity trap: where character assignment
appears as an eligibility or control plan, LEN is checked explicitly rather
than inferred from a comparison, because comparison blank-pads the shorter
operand and would succeed for the wrong reason. And no plan assumes ISO10646
or ASCII kinds exist — the kind facets are profile-qualified and skipped when
unavailable rather than approximated.

There were no blocking findings; two non-blocking observations are recorded.

With this batch, Clause10 source is complete for all of10.1 and for10.2.1.
10.2.2,10.2.3 and10.2.4 remain.

There remain **2,083cases**, now with **213catalogues,1,226requirements,
1,788direct,22linked and4,102pending facets out of5,912**. Source accounting
covers2,078base units. All2,083case bindings,2,047reviews,209older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked.
See `doc/source_audits/batch_106.json`.

The hundred-and-seventh checkpoint registers the independently reviewed
pointer assignment statement source:32base/61fine units across10.2.2.1 and
10.2.2.2,29requirements and92pending facets.

10.2.2.2 is the most **constraint-dense** subclause registered so far:27 of
its30base units are numbered items — R1034 through R1041 and C1016 through
C1034 — all of which were already accounted by the numbered-rule inventory.
So the packet newly accounts only **five** base units:10.2.2.1p1 and p2, and
10.2.2.2's unnumbered note, p1 and p2. The reviewer verified all27
individually and found no double count and no dropped unit.

The zero-permissions verdict here is unusually clean. The words "may", "need
not", "is permitted to" and "processor dependent" **do not occur in this scope
at all**. The only latitude-shaped word is "can", twice: once in10.2.2.1p2,
where pointer assignment for a pointer component of a structure *can also take
place* by execution of a derived-type intrinsic assignment statement — a
second semantic route, not a processor choice — and once in a NOTE observing
that a coarray can be of a derived type with pointer or allocatable
subcomponents, which describes an admitted program shape.

10.2.2.2p1 and p2 are dispositioned as **definitions**, and the reviewer
confirmed that is right rather than an under-claim: p1 states what
*data-pointer-object*, *proc-pointer-object*, *data-target* and *proc-target*
denote, and p2 defines the pointer object and target for a derived-type
intrinsic assignment. Neither carries a `shall`, and no normative obligation
was lost by treating them as definitions.

The32-row attribution table was **audited rather than accepted**, under the
precedent established in batch105. Every constraint that yields two or more
negatives was examined to confirm each negative is individually attributable
to one prohibiting clause, rather than a single program violating a constraint
in two ways at once; C1018, C1019, C1020, C1021, C1023, C1026, C1028, C1030,
C1031, C1032 and C1033 were checked against the source.

The pointer-specific discipline is the part worth recording for later. **No
plan reads, compares, dereferences, invokes or inquires about a pointer whose
association status is undefined** — such a program is not conforming, and the
catalogue explicitly forbids `ASSOCIATED` or any other inspection in that
state. `ASSOCIATED` is proposed only after some other cited source has
established defined status, with16.9.20 retained as an explicit dependency so
the oracle is not circular. And no bounds oracle is asserted without nondefault
bounds, because a bound that coincides with the default proves nothing.

There were no blocking findings; three non-blocking observations are recorded.

There remain **2,083cases**, now with **215catalogues,1,255requirements,
1,788direct,22linked and4,194pending facets out of6,004**. Source accounting
covers2,083base units. All2,083case bindings,2,047reviews,213older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked.
See `doc/source_audits/batch_107.json`.

The hundred-and-eighth checkpoint registers the independently reviewed data
and procedure pointer assignment source:20base/46fine units across10.2.2.3,
10.2.2.4 and10.2.2.5,20S requirements and64pending facets. **No numbered
item falls in this scope at all** — R1034 through R1041 and C1016 through
C1034 all live in10.2.2.2 — so all20base units are newly accounted. The
reviewer verified that claim independently rather than taking it from the
parallel batch107 author.

This packet and batch107 were authored **in parallel** from the same base,
splitting10.2.2 between them. Neither author read the other's worktree; both
read the neighbouring sections from the pinned document to place the boundary.
That makes the boundary the thing most worth checking, and the reviewer
checked it in both directions. The split that needed scrutiny is a fine one:
bounds **remapping effects** in p8 through p10 are owned here, while bounds
**syntax and count constraints** are delegated to10.2.2.2. That is exactly the
kind of division where a hole can open, and none was found — nor any
duplication.

10.2.2.5 yields **zero requirements and zero facets**, because it is examples.
Both its base units and all three fine units are still accounted; the zero
records the absence of a testable obligation, not an omission.

Three permissions are recorded, all in10.2.2.4p3: the pure, simple and
elemental-intrinsic target exceptions. Each is an *allowed exception* rather
than an obligation that anything be exercised. No other unit in scope grants
latitude, and nothing was demoted.

The attribution table needed verifying word by word here for a specific
reason: **every row cites a `shall` from a paragraph rather than from a
numbered constraint.** That is legitimate — a paragraph can prohibit — but it
removes the convenient signal a C-number provides. The reviewer checked the p7
VOLATILE "if and only if" family, which yields four facets from one sentence;
the three separate facet families p8 carries; and the opposite implicit-
interface pairs in10.2.2.4p5, confirming the source really states both
directions.

The pointer discipline here is worth recording precisely, because it shows the
right *shape* for an unobservability claim. The plans for the p2 remote-image
undefined status, the p5 undefined-status target exclusion and the p8
undefined remap target do not read, compare, inquire about or otherwise
observe a pointer once its association status becomes undefined. But the claim
is **scoped to undefined association status only** — conforming controls may
still check parameter values, association, bounds, extents or procedure calls
wherever the source rule requires a defined state. An unobservability claim
that swept wider than that would itself be a defect. Bounds evidence is
non-vacuous by construction: nondefault lower bounds, remapped shapes that
differ from the target's, and target lower bounds distinct from the explicit
ones.

With this batch,10.2.2 is source-complete.

There remain **2,083cases**, now with **218catalogues,1,275requirements,
1,788direct,22linked and4,258pending facets out of6,068**. Source accounting
covers2,103base units. All2,083case bindings,2,047reviews,215older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked. Several10.2.2.4facets depend on unregistered Clause15
material and cannot be implemented until it is registered.
See `doc/source_audits/batch_108.json`.

The hundred-and-ninth checkpoint registers the independently reviewed masked
array assignment source — the `WHERE` statement and construct:30base/57fine
units across10.2.3.1 and10.2.3.2,28requirements and75pending facets. All
twelve numbered items, R1042 through R1050 and C1035 through C1037, are in
10.2.3.1 and were already accounted;10.2.3.2 contains none, so18base units
are newly accounted. The reviewer verified that by **recomputing the suite
accounting algorithm** against the base commit rather than trusting the
author's arithmetic.

The heart of this subclause is the **control mask and pending control mask**,
and it is the easiest thing in Clause10 to paraphrase almost-correctly. The
author flagged it as their own highest risk. So the reviewer derived all eight
transitions from the source *before* looking at the catalogue:

- A top-level `WHERE` statement or construct statement evaluates *mask-expr*
  and sets the control mask to it; a top-level construct also sets the pending
  control mask to `.NOT. mask-expr`.
- Each `WHERE`, construct and masked `ELSEWHERE` mask is evaluated **at most
  once** per execution of that statement.
- A **masked `ELSEWHERE`**, with `mc` the previous pending mask, first sets the
  control mask to `mc`, then sets pending to `mc .AND. .NOT. mask`, then sets
  control to `mc .AND. mask`.
- A bare `ELSEWHERE` takes the current pending mask and establishes no new one.
- `END WHERE` restores both masks.
- And the distinction that matters: a nested `WHERE` **construct** sets pending
  to `mc .AND. .NOT.` inner and control to `mc .AND.` inner, whereas a nested
  `WHERE` **statement** sets the control mask and **does not alter pending** at
  all.

The catalogue states all eight directly from p1 through p8, keeps the nested-
construct and nested-statement cases separate, and — importantly — no
requirement or facet leans on the subclause's example as authority.

Exactly one permission is recorded, and its scope is the point. p13 says the
execution of a function reference in the mask expression of a `WHERE`
**statement** is permitted to affect entities in the assignment statement —
expressly the statement, not a construct statement and not a masked
`ELSEWHERE`. The catalogue keeps that scope. Equally important is what is
*not* a permission: there is **no local element-assignment-order latitude** in
10.2.3 at all. p3 orders statements within a construct and p12 selects which
elements are assigned; neither licenses an arbitrary per-element order. So
leaving per-element assignment order, snapshot and temporary issues to the
registered10.2.1.3 is correct rather than a demotion.

The masking oracle discipline is the valuable part for later fixture work.
Assignment to elements *not* selected by the mask is directly observable, and
the plans make it non-vacuous: unselected elements are preloaded with values
**different from every right-hand-side value**, so the assertion cannot
succeed for the wrong reason. No plan computes expected masking with `MERGE`,
`PACK`, `COUNT` or any equivalent intrinsic — that would duplicate the feature
under test. The p2 "at most once" facets are source-control only, with no
call-count oracle. And the unobservability limits are scoped precisely to
order, call counts, side effects, temporaries, short-circuiting and storage —
they are not used to suppress directly observable branch membership.

There were no blocking findings; two non-blocking observations are recorded.

Only10.2.4 now remains to complete Clause10 source.

There remain **2,083cases**, now with **220catalogues,1,303requirements,
1,788direct,22linked and4,333pending facets out of6,143**. Source accounting
covers2,121base units. All2,083case bindings,2,047reviews,218older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked.
See `doc/source_audits/batch_109.json`.

The hundred-and-tenth checkpoint registers the independently reviewed `FORALL`
source:28base/62fine units across10.2.4.1,10.2.4.2.1 through10.2.4.2.4,
10.2.4.3 and10.2.4.4,33requirements and77pending facets. Ten numbered items —
R1051 through R1056 and C1038 through C1041 — were already accounted, so18base
units are newly accounted.

**With this batch, Clause10 source registration is complete.** All53Clause10
catalogues are reviewed, every content-bearing Clause10 section has a
catalogue, and338Clause10 base units are accounted. Clauses8,9 and10 are now
source-complete.

`FORALL` is the richest remaining source of processor latitude in Clause10,
and the entire value of this registration turns on one line: what the standard
**requires** about the final state, versus what it merely **permits** about
order. The reviewer derived that line independently from the source before
comparing. The rules about when each right-hand side is evaluated relative to
the assignments are the only reason `FORALL` is testable at all, and the
catalogue neither strengthens nor weakens them.

Six permissions are recorded and each was verified in both directions: the
any-order evaluation and assignment latitude of10.2.4.2.4p2, the corresponding
pointer evaluation and association latitude of p3, the10.2.4.4p1 permission to
assign or pointer-assign the same object in *different* statements, and the
p2 permission for a nested concurrent header to depend on outer index values.
No plan anywhere asserts that the processor took a particular order, counts
function calls, relies on a side effect, or observes a temporary — a program
able to detect the processing order would not be a conforming test.

The reviewer audited **all21** diagnostic-obligation facets rather than a
sample. Three families needed real scrutiny: the four C1038 rows, which all
cite the identical words "shall have the same forall-construct-name" and had to
be shown to differ in exactly one property each; the five C1040 rows citing
"shall be a pure procedure" across function reference, defined operation,
defined assignment and finalization, where the source does extend to all four;
and the10.2.4.4 many-to-one rows, checked specifically to confirm the invalid
programs are not *also* non-conforming for a purity, index-definition or
conformability reason. None was found wanting.

The ownership boundaries were checked in both directions. Assignment
conversion, element correspondence, character padding and truncation, and
allocatable and component assignment remain with10.2.1.3; pointer-assignment
effects with10.2.2; `WHERE` control-mask semantics with10.2.3, the `FORALL`
overlay being confined to10.2.4.2.4p5. There were no blocking findings.

One thing this milestone is **not**. Completing Clause10 *source registration*
is not completing Clause10 *testing*. Clause10 now declares1,731facets, of
which all but a handful are pending, and no Clause10 fixture has yet been
written. Several facets additionally depend on unregistered Clause11
(11.1.7 `DO CONCURRENT`, branch targets), Clause15 (pure procedures,
finalization) and Clause19 (index-name scope, pointer association status)
material, and cannot be implemented until those clauses are registered.

There remain **2,083cases**, now with **227catalogues,1,336requirements,
1,788direct,22linked and4,410pending facets out of6,220**. Source accounting
covers2,139base units. All2,083case bindings,2,047reviews,220older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked.
See `doc/source_audits/batch_110.json`.

The hundred-and-eleventh checkpoint **opens Clause 11**. Nothing in Clause 11
was registered before this batch, so it establishes the shape later Clause 11
packets will follow:44base/77fine units across11.1.1 Blocks,11.1.2.1 Control
flow in blocks,11.1.2.2 Execution of a block,11.1.3.1 through11.1.3.4 the
ASSOCIATE construct, and11.1.4 the BLOCK construct —42requirements and
119pending facets. Twenty numbered items were already inventoried, so24base
units are newly accounted.

One precedent set here will recur throughout Clause 11 and deserves recording.
The standard repeatedly says it is permissible to branch to an `END` statement
**only** from within its construct. That single sentence does *two* things: it
**permits** the inward branch, and through the word "only" it **prohibits** the
outward one. Recording only the permission loses a restriction; recording only
the restriction loses a permission. The reviewer confirmed the packet captures
both halves in each case. The other permission worth naming is11.1.4p3, which
grants explicit processor latitude over specification-expression evaluation
order — recorded as latitude, with no plan asserting the processor took any
particular order.

The attribution table was audited in full —all30negative rows, not a sample.
Three families needed real scrutiny. The **R1109** row is the interesting one:
its quoted prohibiting words are a **grammar production**, not a `shall`. A
syntax rule can support a negative, but this is precisely the shape that has
produced defects before, so it was adjudicated against how earlier batches
treated R-rule negatives, and accepted. The **seven C1107 rows** all derive
from one prohibition list — COMMON, EQUIVALENCE, INTENT, NAMELIST, OPTIONAL,
statement functions, VALUE — and each had to be shown individually
attributable and not rejectable for a second reason. And the **C1101** and
**11.1.3.3p5** rows quote long compound sentences, where each negative must
isolate exactly one clause.

Two things were checked for *under*-claiming, which this project treats as no
less a defect than over-claiming. The author dispositioned **C1104** as
source-classification only, reasoning that ordinary pointer assignment is
conforming through the `variable` selector alternative so no standalone
negative exists; the reviewer examined that independently and agreed. And
**11.1.3.4** yields zero requirements and zero facets because it is examples,
with its single note base unit and fine unit still accounted.

What `ASSOCIATE` makes observable is genuinely valuable: the associate name's
type, type parameters, rank, bounds and definability, and construct-entity
scoping. The plans are non-vacuous — bounds coinciding with the selector's
would prove nothing, and an outer variable already holding the expected value
would prove nothing about scoping. Length facets assert `LEN` explicitly rather
than relying on character comparison, which blank-pads the shorter operand.

Two limits are recorded honestly. **Branch-to-`END` negatives cannot be
implemented at all** until11.2 registers branch statement syntax and
semantics, and the11.1.3.3p3 `CHANGE TEAM` plans are dependency-only until
11.1.5 owns that construct.

There remain **2,083cases**, now with **235catalogues,1,378requirements,
1,788direct,22linked and4,529pending facets out of6,339**. Source accounting
covers2,163base units. All2,083case bindings,2,047reviews,227older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked.
See `doc/source_audits/batch_111.json`.

The hundred-and-twelfth checkpoint registers the independently reviewed
`CHANGE TEAM` and `CRITICAL` source:39base/75fine units across11.1.5.1,
11.1.5.2 and11.1.6,33requirements and85pending facets. Eighteen numbered
items were already accounted — twelve in11.1.5.1, **none** in11.1.5.2, six in
11.1.6 — so21base units are newly accounted.

A process point first. The authoring prompt for this packet **wrongly guessed**
that these sections were the `IF` and `CASE` constructs. The author read the
pinned document, found they are `CHANGE TEAM` and `CRITICAL`, and registered
what the source actually says. The reviewer verified the titles independently
and recorded the override as correct. That is the right precedent: **the
pinned source outranks the coordinator's instruction**, and an author who
follows a wrong prompt into the wrong sections would have done real damage.

The substantive problem in this scope is that `CHANGE TEAM` and `CRITICAL` are
fundamentally about **multi-image execution**, and this suite has no
multi-image testing capability. Almost every interesting obligation is a
dynamic cross-image requirement that no conforming single-image program can
observe and that a processor is not required to diagnose.

That produced finding **C11TR-001**. The rule at11.1.5.2p5 — *"All active
images of the new team shall execute the same CHANGE TEAM statement"* — had
been filed as a **diagnostic rejection**, a negative with a control expecting
the processor to reject the invalid program. But which `CHANGE TEAM` statement
each image executes is determined at run time by which image runs which code
path. A conforming processor is neither required to diagnose a violation nor
generally able to, and there is no portable executable oracle either, because
observing that images diverged would require exactly the timing, scheduling and
interleaving evidence this project forbids. The facet was unimplementable in
**both** directions. The requirement stays registered and still states the p5
obligation; only the unsupportable plan was removed.

The rule that closes it generalises, and is now a project precedent:

> A facet may carry a **diagnostic** expectation only if a conforming
> processor is actually required to reject the program, and an **executable**
> oracle only if a conforming single-image program can portably observe the
> effect. A dynamic multi-image synchronization obligation satisfies neither.

The author then swept the whole packet against that test and produced a
22-row classification. It reclassified **eight further facets** beyond the one
found — the successful-change-team synchronization, the post-change and
post-`END TEAM` segment delays, cross-image segment precedence, and, notably,
the `CRITICAL` one-image-at-a-time and mutual-exclusion facets. `CRITICAL`
does provide mutual exclusion, but a conforming program cannot portably
observe that another image was excluded.

Crucially, the reviewer audited that sweep for **over-correction** as well as
under-correction, because an unobservability claim that is too broad is itself
a defect here. The team-restoration rows and the `CRITICAL` segment
classification were examined specifically for local single-image
observability. None was over-suppressed, nothing is missing from the table,
and no facet could pass vacuously in a single-image run — which would be worse
than having no facet at all.

Both permissions follow the batch111 precedent: the "permissible to branch …
**only** from within" sentences carry a permission and a paired restriction,
and both halves are captured.

The honest summary is that a substantial fraction of this packet's85facets are
recorded as **unimplementable** in the current observational regime rather
than merely unwritten. Registering this source gives the suite no multi-image
capability; acquiring one would be separate and substantial work.

There remain **2,083cases**, now with **238catalogues,1,411requirements,
1,788direct,22linked and4,614pending facets out of6,424**. Source accounting
covers2,184base units. All2,083case bindings,2,047reviews,235older
catalogues,22links,R402 and the `b153c75b` baseline are preserved, and no
compiler was invoked.
See `doc/source_audits/batch_112.json`.

The hundred-and-fourteenth checkpoint registers the independently reviewed
`DO` construct **execution** source, including `DO CONCURRENT`:50base/115fine
units across11.1.7.4.1 through11.1.7.4.5,11.1.7.5 and11.1.7.6,43requirements
and125pending facets. Ten numbered items were already accounted, so40base
units are newly accounted — the non-numbered paragraphs, the notes, and
Table11.1.

This is the most **latitude-dense** material in Clause 11, and almost all of
its value depends on getting two intricate things exactly right.

The first is **locality**. The reviewer derived `LOCAL`, `LOCAL_INIT`,
`SHARED`, `REDUCE` and unspecified locality from the source before looking at
the catalogue, and verified **Table 11.1 row by row**, since extraction
interleaves its columns. The rule that governs everything else is this: a
variable with `LOCAL` locality is **undefined** at the start of each iteration
— except for default-initialized subobjects — and undefined again after the
construct. Reading, comparing or inquiring about it in that state is not a
conforming program at all. No plan does. Equally important, that
unobservability claim is **scoped to exactly that state**: it does not
suppress the final value of a `SHARED` or `REDUCE` variable after the
construct, which remains plainly observable.

The second is the **reduction trap**. The processor may combine `REDUCE`
values in **any order**. Real and complex values are approximations under
7.4.3, and 10.1.5.2.4 permits mathematically equivalent rewriting. A floating
reduction is therefore order-sensitive, and **no `REDUCE` result over reals
may be a value oracle**. Only order-insensitive integer and logical reductions
are planned.

Five permissions are recorded: any-order evaluation of the concurrent limit
and step expressions; any-order execution of `DO CONCURRENT` iterations; the
`CYCLE` curtailment effect; the processor's freedom to combine `REDUCE` values
in any order; and processor-dependent sequential record ordering across
iterations. No plan infers an iteration order, counts invocations, relies on a
side effect, or observes a temporary — a program able to detect the order is
not a conforming test.

This packet produced two tables rather than one. Alongside the usual
**attribution** table, the author supplied an **implementability** table
classifying every facet as implementable, source-control only, or
unimplementable and context-dependent — the discipline established in
batch112. The reviewer audited it **in both directions**: nothing marked
unimplementable turned out to be observable by a conforming single-image
program, and nothing marked implementable secretly required order, timing or
multi-image observation, or could pass vacuously. The paragraph-level `shall`
rules in11.1.7.5 needed the most care, since several are obligations on the
program that a processor is not required to diagnose; each was adjudicated
individually rather than swept into one category.

11.1.7.6 yields zero requirements and zero facets because it is examples, with
all six note base units still accounted. There were no blocking findings.

A real limit: several restrictions — C1143 on purity, C1145 and C1146 on the
IEEE modules — depend on **unregistered Clause 15 and Clause 17** material and
cannot be implemented until those clauses are registered.

There remain **2,083cases**, now with **245catalogues,1,454requirements,
1,788direct,22linked and4,739pending facets out of6,549**. Source accounting
covers2,224base units. `authored_facets` is unchanged at1,788 and the fixture
review states are unchanged at1,770/274/1 — this packet touches nothing under
`tests/` and claims no execution credit. All2,083case bindings,2,047reviews,
238older catalogues,22links,R402 and the `b153c75b` baseline are preserved,
and no compiler was invoked.
See `doc/source_audits/batch_114.json`.

The hundred-and-thirteenth checkpoint registers the independently reviewed
`DO` construct **form and loop control** source:40base/78fine units across
11.1.7.1,11.1.7.2 and11.1.7.3,38requirements and110pending facets. It is the
most instructive batch of the session, because it exposed a structural
coupling in the suite that no previous batch had hit.

The packet was blocked with two findings. **C11DFR-001**: it had added
`! covers` metadata headers to **four pre-existing fixture files**, binding ten
facets to them. That raised `authored_facets` from1,788 to1,798 and — measured
by the reviewer — **staled four reference-validated review groups**. Source
registration is not fixture approval and confers no execution credit; every
other source packet in this project has left the case corpus untouched.
**C11DFR-002**: a single file-level `covers` line bound `R1123_invalid` to
*four* distinct negatives at once, when that file contains four isolated
subroutines each exercising a different grammar defect — overbroad, and
destructive of per-facet attribution.

Removing the bindings then made the audit **abort**:
`ERROR: C1121_invalid:character: missing, duplicate, or unknown catalogue
facets`. The cause, diagnosed directly in `tests/suite_data.py`, is a genuine
coupling rather than an author error. `validate_case_requirement` is invoked
only when `self.requirements.get(case.rule)` is truthy, and it raises on an
empty facet list; meanwhile the parser requires a `covers` header only for
`S<section>-NNN` rules, not for numbered ones. So before this packet, `C1121`
and `R1123` were not catalogued requirements and their legacy cases were
skipped entirely. **Registering them structurally forces those cases to gain
`covers` metadata.**

That left exactly two consistent outcomes: register the requirements *and*
bind the fixtures, or do not register the requirements. A source packet may
not do the former. So this was ruled a **fixture migration** — for which the
ledger already shows precedent as a dedicated batch type, in the earlier C801
and C815 migrations, each with independent fixture review and explicit
retained-identifier accounting.

The two requirements were therefore **deferred, not dropped**. `C1121`,
`R1123` and their fine units are dispositioned `unresolved` and remain fully
**accounted** — they do not vanish from the census — each carrying an explicit
rationale naming the reason and the migration followup. The arithmetic follows
honestly: seven non-numbered base units are newly accounted, but two
previously-accounted numbered units move into unresolved, so the net global
delta is **+5 accounted base units and +4 unresolved fine units**. The
reviewer confirmed independently that this is an honest deferral rather than a
quiet drop, and the right source-only outcome rather than under-claiming.

Everything else stands: the31 registered numbered requirements, the two
permissions — including the `end-do` "only from within" sentence split into
both a permission and a restriction, per the batch111 precedent — and the
deliberate decision **not** to own the iteration-count rule or the post-loop
`DO` variable value, which belong to11.1.7.4 and were recorded as dependencies
instead. The attribution audit covered the R1123 grammar-production row, the
C1121/R1124 overlap, and the C1130 and C1131 exclusion lists.

`authored_facets` is back to **1,788**, the fixture review states are restored
to **1,770/274/1 with zero stale groups**, and the `tests/` directory is
byte-identical to its state before the packet.

There remain **2,083cases**, now with **248catalogues,1,492requirements,
1,788direct,22linked and4,849pending facets out of6,659**. Source accounting
covers2,229base units, with4,244base and **10** fine units unresolved — four
of those fine units, and two base units, are the deliberate deferrals recorded
above.
See `doc/source_audits/batch_113.json`.

The hundred-and-fifteenth checkpoint registers the independently reviewed
`IF` construct and `SELECT CASE` source:39base/81fine units across11.1.8.1
through11.1.8.4 and11.1.9.1 through11.1.9.3,36requirements and95pending
facets. Twenty-two numbered items were already accounted, so17base units are
newly accounted. The authoring prompt deliberately did **not** name the
constructs — the author established them from the source, and the reviewer
verified the titles independently.

The `SELECT CASE` **matching rules** are the substance here, and the reviewer
derived them from the source before looking at the catalogue: which case value
ranges match which selector values, that **at most one** block is selected,
how ranges with an omitted lower or upper bound behave, and when `CASE
DEFAULT` is selected.

The trap worth recording is the **character selector**. C1152 explicitly
*allows* a case value and the selector to have different character lengths —
and character comparison blank-pads the shorter operand. So a length-differing
match is genuinely meaningful, but a plan that relies on that *accidentally*
proves nothing. The packet states the semantics explicitly rather than
inferring them, and no plan assumes a particular character kind exists.

Four permissions were adjudicated, and two of them were interesting. The
`END IF` and `END SELECT` "permissible … **only** from within" sentences again
carry both a permission and a restriction, and both halves are captured per
the batch111 precedent. The **11.1.8.4p3** side-effect permission was accepted
but with an explicit **double-credit caution**: 10.1.4 already owns general
evaluation latitude and side effects, and future fixture work must not claim
the same latitude under both owners. And **C1152's** "lengths may differ" was
examined specifically for whether it is a genuine permission or merely an
*absent restriction* — those are not the same thing, and a non-restriction
dressed as a permission would be a classification error. It was accepted as an
explicit permission.

The attribution audit covered the four rows — R1137, R1141, R1146, R1149 —
whose prohibiting words are **grammar productions** rather than a `shall`, a
shape that has produced defects before; the four C1147 and three C1149
construct-name rows; and the three **C1154** rows, which all cite the
*identical* clause "no possible value matches more than one case-value-range".
Three negatives from one clause needs each to be individually attributable,
and the character-padding overlap row in particular checked as not rejectable
for a second reason.

The observability discipline is the general lesson for selection constructs:
**which block executed is plainly observable; which condition or selector was
evaluated is not**, and Fortran guarantees no short-circuiting anywhere. The
plans assert only which block ran, using sentinels distinct from every value
any block could write. Crucially, the unobservability claim is scoped so that
it does not suppress the block-selection fact — an overbroad claim would
itself be a defect.

11.1.8.3 and11.1.9.3 each yield zero requirements and zero facets because they
are examples, with all base and fine units still accounted. There were no
blocking findings.

With this batch,11.1 is registered through11.1.9;11.1.10 to11.1.12 and11.2
to11.7 remain.

There remain **2,083cases**, now with **255catalogues,1,528requirements,
1,788direct,22linked and4,944pending facets out of6,754**. Source accounting
covers2,246base units. `authored_facets` is unchanged at1,788 and `tests/` is
untouched. All2,083case bindings,2,047reviews,248older catalogues,22links,
R402 and the `b153c75b` baseline are preserved, and no compiler was invoked.
See `doc/source_audits/batch_115.json`.

The hundred-and-seventeenth checkpoint registers the independently reviewed
`SELECT TYPE` construct and `EXIT` statement source:35base units across
11.1.11.1,11.1.11.2,11.1.11.3 and11.1.12,30requirements and89pending facets.
Seventeen numbered items were already accounted, so18base units are newly
accounted. The authoring prompt did not name the constructs; the author
established them from the source and the reviewer verified the titles
independently.

The first thing this packet got right was **not** walking into the trap that
blocked batch113. Before registering any numbered rule, the author checked
whether `tests/` already held cases for it — because registering a numbered
rule that already has legacy fixtures *structurally forces* binding them, and
a source packet must never do that. None of R1154–R1158 or C1162–C1173 had
pre-existing cases, so registration was safe and nothing needed deferring. The
reviewer confirmed that check independently.

The substance is the **type-guard matching rule**, and it was derived from the
source and verified word for word, because it is the single easiest thing in
Clause 11 to paraphrase almost-correctly. A `TYPE IS` guard matches when the
dynamic type *and kind type parameter values* are the same as specified. A
`CLASS IS` guard matches when the dynamic type is an extension of the
specified type. Selection then prefers a matching `TYPE IS`; failing that, a
unique matching `CLASS IS`; failing that, among several matching `CLASS IS`
guards, the one specifying **a type that is an extension of all the types
specified in the others**; failing that, `CLASS DEFAULT`; failing that, no
block is selected.

There is **no processor latitude anywhere in this scope**, and none was
invented — the single permission is the11.1.11.2p9 internal branch to
`end-select-type-stmt`, whose "only" wording again supplies the paired
restriction.

Two subtle readings were checked and **confirmed correct**, both of which a
careless packet would have got wrong in the direction of over-claiming.
**C1168** does *not* prohibit one `TYPE IS` guard together with one `CLASS IS`
guard specifying the same type; it prohibits the same type appearing in more
than one `TYPE IS`, and in more than one `CLASS IS`, separately. And **C1172**
is *not* a blanket ban on a textual `EXIT` inside a `DO CONCURRENT` construct
— it turns on which construct the `EXIT` **belongs to**, and the negatives
isolate exactly that property.

The boundary against11.1.3.3 was checked in both directions: this packet owns
the syntax, guard matching, selected-block semantics, associate-name choice
and the p5–p7 associating-entity type and declaration changes, while11.1.3.3
retains rank and bounds, corank and cobounds, `ASYNCHRONOUS` and `VOLATILE`,
`OPTIONAL` absence, contiguity and definability transfer. No plan uses
`SAME_TYPE_AS` or `EXTENDS_TYPE_OF` as an oracle basis, since that would
duplicate the feature under test, and the guard-evaluation unobservability
claim is scoped so it does not suppress the observable block-selection fact.
11.1.11.3 yields zero facets because it is examples. There were no blocking
findings.

There remain **2,083cases**, now with **259catalogues,1,558requirements,
1,788direct,22linked and5,033pending facets out of6,843**. Source accounting
covers2,264base units. `authored_facets` is unchanged at1,788 and `tests/` is
untouched.
See `doc/source_audits/batch_117.json`.

The hundred-and-sixteenth checkpoint registers the independently reviewed
`SELECT RANK` construct source:21base/47fine units across11.1.10.1 through
11.1.10.4,21requirements and63pending facets. Eleven numbered items were
already accounted, so10base units are newly accounted.

**With this batch, 11.1 is source-complete: 268 of 268 base units**, across
11.1.1 through11.1.12.

The author ran the **pre-existing-fixture check** over R1150–R1153 and
C1155–C1161 without being prompted by a failure, and found none. That is what
kept this packet out of the trap that blocked batch113 — registering a
numbered rule that already has legacy fixtures structurally forces binding
them, which a source packet must never do. The reviewer confirmed the check
independently.

The blocking finding, **C11SRR-001**, is a good example of a defect that is
easy to miss because the text reads as one rule. C1161's first sentence says
that if the `SELECT RANK` statement specifies a construct name, the
corresponding `END SELECT` **shall specify the same** name. That is *two*
obligations: the name must be **present**, and it must be **the same**. The
packet had a negative for a wrong name, and the mirror-image negative for an
unnamed construct with a named `END SELECT` — but nothing at all for a
**named construct with an unnamed `END SELECT`**. A distinct prohibition was
left with no oracle row. The correction added
`named-select-rank-unnamed-end-rejected`, whose control differs in exactly one
property: the presence of the name.

Because that is a *class* of defect rather than a one-off — a compound `shall`
sentence whose second obligation goes unnoticed — a **compound-obligation
sweep** was demanded across the whole scope, and then **re-derived from the
pinned document by the reviewer** rather than accepted: C1155 has two
obligations covered by three legitimate facets; C1156 and C1157 one each;
C1158, C1159 and C1160 two each; C1161 three, now covered; and R1150–R1153
carry production alternatives with no omitted compound constraint.

Both permissions were adjudicated, including the specific question of whether
11.1.10.1p3 — a rank value greater than the maximum possible rank is
permitted, and the block never executes — is a genuine *permission* or merely
a statement of *effect*. The11.1.10.2p2 "only from within" sentence is again
split into both a permission and a restriction. The boundary against11.1.3.3
was checked in both directions, this packet owning SELECT-RANK-specific
association, rank matching, rank and bounds, and `ALLOCATABLE`/`POINTER`/
`TARGET` inheritance.

One limit deserves naming: `SELECT RANK` exists to handle **assumed-rank dummy
arguments**, which live in **unregistered Clause 15**. Those facets cannot be
implemented until Clause 15 is registered.

And the larger caveat stands: 11.1 being *source*-complete is not 11.1 being
*test*-complete. Several hundred Clause 11 facets are pending, and **no Clause
11 fixture has been written at all**.

There remain **2,083cases**, now with **263catalogues,1,579requirements,
1,788direct,22linked and5,096pending facets out of6,906**. Source accounting
covers2,274base units. `authored_facets` is unchanged at1,788 and `tests/` is
untouched.
See `doc/source_audits/batch_116.json`.

The hundred-and-eighteenth checkpoint is a **fixture packet** — the first
after sixteen consecutive source packets. It therefore *legitimately* changes
`authored_facets` and the case count, which its predecessors were required to
leave untouched. Six of the eight pending facets of **9.5.3.3, array element
order**, are now established by reference-validated runtime effects; the
corpus moves from **2,083 to 2,089 cases**.

9.5.3.3 was chosen because it gives the subscript order value by an **exact
formula with no processor latitude at all** — unusual among recently
registered material, and precisely what makes it testable. The entire
difficulty is non-vacuity.

The first question was **circularity**. The fixtures use a `DATA` statement to
lay values down in array element order and then read back by subscript — but
9.5.3.3 *is* the definition of array element order, so is that not assuming
what it sets out to show? The reviewer adjudicated it **not circular**, and
the reasoning is worth recording: 9.5.3.3 owns the formula and the sequence,
while the `DATA` statement in 8.6.7 is a legitimate **consumer** of that
ordering rather than a restatement of it; the expected values are
independently hand-computed literal constants; and the read-back is by
subscript, which is independent of the ordering mechanism. No fixture uses
`RESHAPE`, `PACK`, `TRANSFER`, sequence association or any storage-layout
assumption.

The second question was whether the tests actually *discriminate*, and here
the review did the thing that matters: it proved non-vacuity **by mutation
rather than by inspection**. Thirteen mutations were applied — row-major and
transposed `DATA` orderings, **same-multiset value swaps** (which catch an
oracle that checks only the *set* of values rather than their positions), a
**unit-lower-bound mutation** (which catches an off-by-one that unit bounds
would otherwise hide), and perturbed expected literals — and **all thirteen
produced a failing test**. A case that survives mutation establishes nothing;
these do not survive it. The fixtures are built to discriminate: non-unit
lower bounds throughout, distinct extents so a transposed formula is caught,
interior subscripts rather than corners, and coordinate-coded literals so each
element's value encodes its own position.

Every hand oracle was independently recomputed from the source formula with no
discrepancies, including the rank-fifteen value of 16. Table 9.1 was read row
by row from the table itself, and the misplaced rank-fifteen multiplication
sign and stray character were confirmed to be **extraction artefacts** rather
than content — which is exactly why the table-layout facet was left pending.
Both remaining facets are source-review claims rather than executable runtime
effects, and the reviewer confirmed no testable facet was silently dropped.
Leaving a facet pending for a good reason is a fine outcome; writing a
circular test is not.

I reproduced both compiler runs myself before recording any adjudication: 6 of
6 pass under the frozen LFortran `0.65.0-411`, and 6 of 6 under gfortran
16.1.0 with `-std=f2023`, which reports agreement on 6 of 6 cases. **Compiler
consensus is not an oracle** — the hand arithmetic was verified independently
and would have overridden both had they disagreed. No LFortran gap appeared
and `tests/expected_failures.txt` is unchanged.

What this establishes is the subscript order value and the element sequence.
It establishes **nothing** about storage association, sequence association or
physical memory layout. And six cases is six cases: Clause 9 still has
hundreds of pending facets.

There are now **2,089cases**, with **263catalogues,1,579requirements,
1,794direct,22linked and5,090pending facets out of6,906**, and fixture review
states of **1,776 reference-validated /274source-reviewed /1needs-oracle**.
See `doc/source_audits/batch_118.json`.

The hundred-and-nineteenth checkpoint is the first of a **fixtures-only**
round. It establishes **13 of the 15** pending facets of **10.1.5.2.2 integer
division** and **10.1.5.3.1 the character intrinsic operation**, taking the
corpus from **2,089 to 2,102 cases**.

These two subclauses were chosen because the batch101 review singled them out
as the part of the numeric and character material that is **genuinely
portable**. Everything around them is hedged — 7.4.3 makes real and complex
values approximations, and 10.1.5.2.4 lets the processor evaluate any
mathematically equivalent alternative — but these two are exact. Integer
division requires the result to be *the integer closest to the mathematical
quotient and between zero and the quotient inclusively*, which is truncation
toward zero; concatenation appends the right operand to the left and its
length is the sum.

Non-vacuity was again proved **by mutation**. Twenty-eight numeric literals
perturbed by one, nine character literals altered at equal length, three
kind-expression expectations, thirteen completion tokens, an operand-order
swap and a changed `LEN` assertion — all failed as required.

**One mutation survived, and it is recorded rather than glossed.** Appending a
trailing blank to an expected character literal survives for all nine
character value assertions, because **character comparison blank-pads the
shorter operand**. That is the exact trap this project has warned about since
batch099. It is non-blocking only because each value comparison is *paired*
with an explicit `LEN` assertion and with test-module content pins, so a wrong
length is still caught. The design holds as a pair; the value comparison alone
does not.

The second honest limitation concerns the decisive question for integer
division. The standard requires truncation toward zero; the common wrong
implementation is flooring. Only **2 of the 4** integer-division fixtures
actually discriminate between them — the negative-dividend case, where `-8/3`
is `-2` under the standard and `-3` under flooring, and the negative-divisor
case. The other two use operands where truncation and flooring agree, and so
establish the result type and the quotient but say **nothing about the
direction**. That is worth stating plainly rather than reporting "4 of 4
established".

No fixture computes an expected value with `MOD`, `MODULO`, `FLOOR`,
`CEILING`, `INT` or `NINT` for division, or with `TRIM`, `INDEX`, `REPEAT` or
`LEN_TRIM` for concatenation — expected values are hand-computed literals.
Table 10.4 was verified row by row. Two facets were correctly left pending:
nondefault character kinds are processor dependent, and a mixed-kind
concatenation is a diagnostic boundary rather than a runtime effect.

I reproduced both runs before recording: 13 of 13 under the frozen LFortran,
13 of 13 under gfortran 16.1.0 `-std=f2023`, with agreement on 13 of 13. No
LFortran gap appeared and `tests/expected_failures.txt` is unchanged.

There are now **2,102cases**, with **1,807direct facets** and **5,077pending**,
and fixture review states of **1,789 reference-validated /274/1**.
See `doc/source_audits/batch_119.json`.

The hundred-and-twentieth checkpoint establishes **22 facets of 10.2.3.2** —
the `WHERE` masking semantics — taking the corpus from **2,102 to 2,124
cases**. It is also **the first baseline change of the session**:
`tests/expected_failures.txt` had been byte-identical for thirty-five
consecutive batches, and now gains three lines, going from 804 to 807.

Those three lines are the point of the whole exercise. The packet found
**three genuine defects in the frozen LFortran target**.

All three are `S10.2.3.2-006` restoration cases —
`nested_construct_restores_outer_control`,
`nested_construct_restores_outer_pending` and
`nested_stmt_restores_outer_control`. They pass under gfortran f2023 and fail
under LFortran. That asymmetry alone proves nothing: a fixture can be wrong in
a way one compiler happens to tolerate, and **compiler consensus is not an
oracle**. So the reviewer **hand-derived the required final arrays from the
source rules**, independently of any compiler:
`[1101,1202,303,304,1205,1106]` for the two nested-construct cases and
`[1101,198,-803,-804,195,1106]` for the nested-statement case. They match the
fixtures. LFortran computes **stale-sentinel values** for the post-construct
elemental update — 199 and 194 where 198 and 195 are required — a sequencing
and stale-right-hand-side defect around `END WHERE` restoration.

So the fixtures are right and the compiler is wrong. The three were recorded
as XFAILs in a **separate execution operation** from the review recording, as
the protocol requires. No fixture was weakened, no oracle relaxed, no
workaround introduced. The defect is also logged as a cross-batch followup, as
a good candidate for an upstream minimal reproducer.

Non-vacuity was again proved **by mutation**, and this packet's campaign is
the most thorough yet: ignoring the mask failed 22 of 22; inverting it failed
22 of 22; perturbing an expected element failed 22 of 22; a masked `ELSEWHERE`
using its own mask alone, without conjoining the previous pending mask, failed
6 of 6; suppressing `END WHERE` restoration failed 3 of 3. And the most
valuable result: **treating a nested construct as a statement failed 5 of 5,
and treating a nested statement as a construct failed 1 of 1.** That
distinction — a nested `WHERE` **construct** alters the pending mask while a
nested `WHERE` **statement** does not — is the subtlest thing in the
subclause, and failing in *both* directions is what makes it genuinely
established rather than assumed.

The fixtures are built to discriminate: sentinels distinct from every value
any branch could write, masks that are never all-true or all-false, integer
and logical data only, and hand-written literal expected arrays. No `MERGE`,
`PACK`, `COUNT`, `UNPACK`, `ALL` or `ANY` appears as an oracle.

What is deliberately **not** claimed matters as much. No element assignment
order is inferred. No mask evaluation is counted — p2 says a mask is evaluated
at most once per execution of its statement, but a conforming program cannot
observe that. Nothing asserts whether an unselected element's expression was
evaluated, since the processor may evaluate more than the context requires.
And the narrow p13 permission for a `WHERE` statement mask function remains a
permission, not an effect claimed as exercised. All 34 facets of 10.2.3.1 and
19 of 10.2.3.2 stay pending for these reasons.

There are now **2,124cases**, with **1,829direct facets** and **5,055pending**,
and fixture review states of **1,811 reference-validated /274/1**.
See `doc/source_audits/batch_120.json`.

The hundred-and-twenty-first checkpoint closes the fixtures-only round with
the **first Clause 11 fixtures in the suite**. Clause 11.1 was source-complete
at 268 of 268 base units but had **no executable tests at all**, so this
packet sets the pattern. Ten facets of **11.1.3.2** and **11.1.3.3** — the
`ASSOCIATE` construct — are established, taking the corpus from **2,124 to
2,134 cases**.

`ASSOCIATE` is unusually good fixture material because the association is
genuinely observable: the associate name's type, kind, length, rank and bounds
are specified; definability means an assignment *through* the associate name
shows up on the selector; and construct-entity scoping is directly testable
against an outer homonym of the same name.

The central claim is that **the associating entity's bounds differ from the
selector's subscripts** — that is exactly where an implementation goes wrong,
and exactly where a careless fixture proves nothing. Mutating the expected
`LBOUND` and `UBOUND` to the selector's subscript values fails, as required.
The reviewer recomputed everything independently: `base(-3:3:2)` has extent 4
and associated bounds 1:4; `base(12:20:3)` has extent 3 and bounds 1:3; the
rank-two strided section has shape `[3,2]`; the character section has length
6. Mutating that `LEN` from 6 to 9 — the parent string's length — also fails,
which is the specific guard against the blank-padding trap. Every length
assertion uses `LEN` explicitly and never a comparison.

One mutation was applied **in the opposite direction**, and it is the nicest
piece of evidence in the packet. Weakening the outer scoping sentinel to a
value written *inside* the construct made the test **stop discriminating** —
it passed. That proves the sentinel choice of 707, distinct from every value
written inside, is doing real work rather than being decorative. Showing that
a design choice *matters* is as valuable as showing the test fails when the
feature breaks.

The inquiry intrinsics `LBOUND`, `UBOUND`, `SHAPE`, `SIZE`, `LEN` and `KIND`
are used as oracles here. That is legitimate **only** because the standard
*requires* the asserted values rather than them being merely typical, and each
plan states that justification; the packet does not claim to be testing those
intrinsics. And `definable-selector-assignment-control` is correctly recorded
as a **positive control** rather than a full effect, because its owning
requirement is a restriction — over-claiming it would have been a defect.

Twenty-three facets stay pending, and every deferral is explicit: polymorphic
selectors need `SELECT TYPE` context; the `END ASSOCIATE` branch facets need
branch-statement ownership from **unregistered 11.2**; coarray and cobound
facets need `CHANGE TEAM` context; the attribute facets need **unregistered
Clause 15** owners; the definability negatives need **Clause 19** scope
isolation; and the kind facet was deferred rather than assume a non-default
kind exists, since availability is processor dependent.

Both runs were reproduced before recording: 10 of 10 under the frozen
LFortran, 10 of 10 under gfortran `-std=f2023`. `ASSOCIATE` with strided
section selectors is precisely where a compiler may be wrong, so it is the
**independently recomputed bounds**, not the agreement between compilers, that
validate these.

There are now **2,134cases**, with **1,839direct facets** and **5,045pending**,
and fixture review states of **1,821 reference-validated /274/1**.

One correction belongs in this record. Binding facets into a catalogue changes
its content, and therefore **stales that catalogue's content-bound source
review** — by design. Batches 118, 119 and 120 each left such staleness
uncorrected and were committed with it. It surfaced only when this batch's
gate **failed**, with `cannot review linked evidence: 11.1.3.3: catalogue
source review is stale`, raised from a linked-evidence test. The earlier gates
had passed purely because no test case happened to exercise those catalogues
through that path — which is luck, not verification.

All six affected source reviews — 9.5.3.3, 10.1.5.2.2, 10.1.5.3.1, 10.2.3.2,
11.1.3.2 and 11.1.3.3 — have been renewed. Each renewal records that the
staleness is attributable **solely** to facet binding, that the **source
accounting is unchanged** (no unit added, removed or redispositioned; no
requirement renumbered or reused), and that it carries the original
independent source review forward without adding any new source claim. The
only remaining non-reviewed catalogue is 18.3.7, which was already `draft` at
the session's starting commit and was never touched. The suite then ran 984
tests OK.

The process lesson is now in the integration checklist: **a fixture packet
must renew the source review of every catalogue it binds facets into, in the
same integration.**
See `doc/source_audits/batch_121.json`.

## Batch 122 — branching, CONTINUE, STOP, FAIL IMAGE and NOTIFY WAIT source

Clause 11.1 has been source-complete since batch118. This packet and its two
parallel siblings close the rest of Clause 11. It registers **11.2.1, 11.2.2,
11.2.3, 11.3, 11.5 and 11.6** — 36 base units over PDF pages 227–231, of which
20 were already counted and **16 are newly accounted**, in six new catalogues
carrying 23 requirements and 64 pending facets. Section titles were again
established **from the source**, not from the coordinator's prompt.

11.4 is the unusual one. `STOP` and `ERROR STOP` were **already registered** in
the pre-existing `stop.json`, so all ten of its base units were already
accounted. This packet therefore adds no 11.4 catalogue and leaves `stop.json`
**byte-unchanged**, merely *relocating* it within `index.json` so the index
stays in section order. The reviewer confirmed the relocation broke nothing and
— importantly — did **not** stale the 11.4 review, because reviews are bound to
catalogue **content**, not to index position.

The reviewer **blocked** the packet. The blocking finding, C11BSR-001, is a
familiar shape: 11.6 p9 collapses into two facets a sentence that actually
carries four obligations — an explanatory message is assigned, the assignment
has intrinsic-assignment semantics, and on success both the definition status
*and* the value are unchanged — while the plan omitted the
**initially-undefined** branch altogether by only ever planning a defined
sentinel. It now carries five facets, mirroring the registered 9.7.5 model
rather than a freshly invented decomposition.

The `ERRMSG` discipline here is absolute and worth restating, because it is
counter-intuitive: the standard leaves `ERRMSG` text **unspecified**, so no
oracle may compare it — not by equality, not by **inequality against a
sentinel**, not by substring, wording, or compiler agreement. That limit was
set by finding SER-005. Only the no-error *unchanged-value* facet has genuine
oracle potential, and even that must assert `LEN` explicitly, because character
comparison blank-pads the shorter operand.

Two further findings were accepted. C11BSR-002 caught a **stale baseline** in
the author's own report: the claimed +26 accounted-base movement was really
**+16**, which the integrator confirmed independently against `df0feaf` = 2274.
The author's 20-already-counted / 16-newly-accounted split had been right all
along; only the reported baseline was wrong. C11BSR-003 caught an **incomplete**
list of the facets that registering 11.2 unblocks. That one matters more than it
looks: the deferred branch-target facets scattered across 11.1.2 through
11.1.11 have no other owner, so anything missing from that list would have been
stranded silently and forever. The widened list — fifteen sites, from
`11.1.2.1` through `11.1.11.2` — is recorded verbatim as the
`clause11-branch-target-facet-migration` followup. None of them is discharged
here; discharging them is fixture work and needs independent fixture review.

The pre-existing fixture check over all fourteen identifiers (`R1159`–`R1167`,
`C1174`–`C1178`) found no legacy cases, so nothing needed deferral — the trap
that blocked batch113.

`FAIL IMAGE` and `NOTIFY WAIT` are **multi-image gated** and unobservable in
this single-image suite, and the exact positive `STAT` value is processor
dependent **latitude**, never a requirement; only positivity and distinctness
from the named `STAT_FAILED_IMAGE` and `STAT_STOPPED_IMAGE` are portable.

One numeric puzzle was settled for good. Two authors reported different fixture
counts from the same base — 1,823 and 1,821. Both are real and measure
different things: the audit reports **1,821 active** review bindings, while raw
`tests/reviews.json` holds 1,823 because `C801_invalid` and `C815_invalid` are
**orphaned** leftovers of an earlier migration, bound to no active case. 1,821
is the audit-active figure; the reviewer who argued otherwise was overruled on
that evidence. It is pre-existing and not a defect, and is recorded here so it
need not be re-investigated the next time someone notices the gap.

Source accounting only: no fixture bound, no case added, no compiler invoked.
`authored_facets` stays at **1,839**, cases at **2,134**, and
`tests/expected_failures.txt` at **807 lines**, byte-unchanged.
See `doc/source_audits/batch_122.json`.

## Batch 123 — image control statements, segments and the SYNC statements

Registers **11.7.1 Image control statements, 11.7.2 Segments, 11.7.3 SYNC ALL,
11.7.4 SYNC IMAGES, 11.7.5 SYNC MEMORY and 11.7.6 SYNC TEAM** — 43 base units
over PDF pages 230–235, of which only 10 were already counted, so **33 are
newly accounted**, in six catalogues with 28 requirements and 74 pending
facets. 11.7.1 and 11.7.2 contain no numbered items at all, which is why their
base units are accounted entirely fresh.

The reviewer **blocked** the packet on two findings, both about decomposition
and disposition rather than about the author's observability judgement, which
was endorsed unchanged.

C117SR-001 is a self-contradiction worth noting: 11.7.4 p1 and p2 collapsed the
*positive*, *upper-bound* and *no-repeated-values* obligations into single
facets — while the packet's **own compound sweep** correctly listed them
separately. The sweep and the catalogue disagreed with each other. They are now
split, all source-control, with **no** diagnostic expectation, because an
out-of-range image set is a value requirement on the *program*, not something a
conforming processor is required to reject.

C117SR-002 is the more consequential. **11.7.2 p3 and 11.7.5 p4 were
dispositioned `permission`** although each carries normative `shall`
restrictions — "shall not be referenced, defined, or become undefined … unless
the segments are ordered", and "shall include a dependency". Only the
atomic/event/notify exceptions, and the sentence saying the dependency
*mechanisms* are processor dependent, are genuine latitude. Both units were
**split** into a requirements half and a permission half rather than merely
re-dispositioned, since each genuinely mixes the two; the reviewer specifically
confirmed the resulting structural parents are not silently emptied of content,
and re-read 11.7.2 to confirm no other ordering `shall` remained misfiled.

That finding matters more than its size suggests. **11.7.2 defines the ordering
model that the whole of 11.7 — and every synchronization statement in the
language — depends on.** Recording its `shall not` restrictions as processor
latitude would have propagated a false permission through every section
downstream. It is also a clean illustration of why latitude is checked in
**both** directions: a requirement misfiled as a permission is exactly as much
a defect as a permission inflated into a requirement.

The correction is what created this packet's **four fine units**, where the
original reported zero; the reviewer confirmed the base count is still 43 and
that nothing was promoted into a base unit or left unaccounted.

Implementability is **26 implementable / 26 source-control / 22
unimplementable-context-dependent**, and the reviewer, required to report
over-suppression as readily as under-suppression, would reclassify nothing.
The unimplementable set is the honest one: synchronization actually occurring,
segment ordering and precedence, timing, scheduling, interleaving, progress,
team membership runtime state, and anything needing a **failed or stopped
image**, which cannot be portably induced. That the majority of this scope
cannot be executed is the correct consequence of the batch112 precedent, not a
coverage shortfall — and it is far better than facets a single-image run would
satisfy **vacuously**.

The pre-existing fixture check over `R1168`–`R1173` and `C1179`–`C1182` found
no legacy cases, including the `SYNC ALL` material flagged as the likeliest to
carry them.

Source accounting only. `authored_facets` stays **1,839**, cases **2,134**, and
`tests/expected_failures.txt` byte-unchanged at **807 lines**.
See `doc/source_audits/batch_123.json`.

## Batch 124 — EVENT, FORM TEAM, LOCK/UNLOCK and STAT=/ERRMSG= — Clause 11 complete

Registers **11.7.7 EVENT POST, 11.7.8 EVENT WAIT, 11.7.9 FORM TEAM, 11.7.10
LOCK and UNLOCK, and 11.7.11 STAT= and ERRMSG= specifiers in image control
statements** — 60 base units over PDF pages 236–241, 20 already counted and
**40 newly accounted**, in five catalogues with 54 requirements and 140 pending
facets. 11.7.11 contains no numbered items at all, so all fourteen of its base
units are accounted fresh.

**This completes Clause 11 at 407 of 407 base units** — the fifth
source-complete clause, after 6, 8, 9 and 10. The contributions are 268 from
11.1 (finished at batch118), 36 from batch122, 43 from batch123 and 60 here;
the total was recomputed independently from `doc/source_inventory.json`, which
gives 67 sections and 407 units for the clause.

Three sections all *start* on page 236, which made mispartitioning the single
largest risk in the packet; the reviewer verified the boundary unit by unit.

The reviewer **blocked** the packet on three findings.

C1177SR-001: all **twenty** "shall not depend" cases were planned as
diagnostic/control pairs. But these are **non-numbered requirements on the
program**, not constraints — no conforming processor is required to reject
them, and dependency is not generally **statically decidable**, so no portable
diagnostic could exist even in principle. All twenty were re-dispositioned as
source-control. That is a re-disposition, not a deletion: every one remains
fully accounted, and the endorsed ten-way obligation split under 11.7.11 p1 was
preserved rather than collapsed.

C1177SR-002 is the most valuable finding of the checkpoint, and it runs in the
*opposite* direction from everything else in 11.7. The packet recorded "no
executable oracle is supplied" for `ACQUIRED_LOCK=` becoming **true** — but for
an **initially unlocked local lock**, a **single-image** program can observe
exactly that. This is **over-suppression**, caught by the standing precedent
that *an unobservability claim which is too broad is itself a defect*. In a
clause where almost everything genuinely is unobservable, the temptation to
blanket-suppress is strongest, and this is where that precedent earns its keep.
The facet was split three ways, with the true-result branch now classified
**implementable**, carrying two recorded prerequisites for whoever writes the
fixture: `LOCK_TYPE` is a coarray, so gfortran needs `-fcoarray=single` and
rejects the syntax by default; and the oracle must set the logical **false
before** the `LOCK` and assert **true after**, so a single-image run cannot
satisfy it **vacuously**.

C1177SR-003: 11.7.11 p5 and p10 collapsed compound effects into STAT-only
facets, dropping the *active-image intended action* and the CRITICAL
*continues-normally* obligation. Both were restored, and an independent
re-sweep of p1 through p13 found no further instance.

The **named-`STAT` list** was independently verified exhaustive: zero on
success, `STAT_STOPPED_IMAGE`, `STAT_FAILED_IMAGE`, `STAT_LOCKED`,
`STAT_UNLOCKED_FAILED_IMAGE`, `STAT_UNLOCKED` and `STAT_LOCKED_OTHER_IMAGE`.
Everything else is processor dependent, and only positivity and distinctness
from the named values may ever be asserted. No `ERRMSG` text, sentinel,
inequality or substring oracle appears anywhere — the SER-005 limit holds.

One small thing was worth not waving through. The correction reported **+3**
declared facets where the described changes implied **+4**. The reconciliation:
the pre-correction 11.7.10 p4 already carried *two* facets, so the three-way
split adds only +1, and +1 plus the two restored facets gives +3. A count gap of
exactly that shape is what concealed the stale-catalogue-review defect at
batch121, so it was reconciled explicitly rather than assumed benign.

Finally, 11.1.6 p4's delegation to 11.7.11 — outstanding since CRITICAL was
registered — is now **discharged**, and the reviewer confirmed the material is
owned here without being duplicated across both catalogues.

One caveat deserves to be stated plainly, because the milestone invites
overreading it: **source-complete is not test-complete.** All 407 base units
carry a disposition and, where applicable, a requirement with an explicit
pending plan. But Clause 11 has only the 45 executable cases added by batches
118–121, and the overwhelming majority of its facets have never been executed.
A great many of them never can be, in a suite with no multi-image capability —
and recording that honestly is better than writing facets a single-image run
would satisfy vacuously.

Source accounting only. `authored_facets` stays **1,839**, cases **2,134**, and
`tests/expected_failures.txt` byte-unchanged at **807 lines**.
See `doc/source_audits/batch_124.json`.

## Batch 126 — the first executable tests Clause 10 has ever had

Clause 10 has been **source-complete since batch110** — 338 base units, every one
classified — and until this batch it had **zero executable fixtures**. Roughly a
thousand pending facets, nothing running. This packet starts closing that gap.

It establishes **14 facets** of **10.1.4 Evaluation of operations**, with 14 new
cases: all three operand-value facets of `S10.1.4-001`, all four
`ac-implied-do` control facets of `S10.1.4-003`, all four elemental binary
facets of `S10.1.4-004`, and three of `S10.1.4-005`.

The reviewer accepted it with **no blocking findings**, which is worth stating
precisely because of *how* it was checked. The reviewer re-read 10.1.4 from the
pinned PDF, **hand-derived every oracle independently** rather than verifying
the author's arithmetic, and **re-ran a sample of the mutation campaign**
instead of accepting the table.

The mutation that matters most is the one the reviewer added: an **absolute-value
implementation simulation**. `-(-7) = 7` on its own is satisfied by a compiler
that computes `ABS` instead of unary minus — the test would pass while the
feature was broken. It is only the paired `-(4) = -4` that rejects that bug.
That pairing is the difference between a test and a decoration, and it is the
pattern every future Clause 10 fixture should copy.

The **reverse mutation** confirmed the other half: removing the `-4` observation
and weakening the check total from 2 to 1 made the mutant **pass**, proving the
check-total sentinel is genuinely load-bearing rather than cosmetic.

All arithmetic here is **exact integer**, which sidesteps the 7.4.3
approximation problem and the 10.1.5.2.4 reassociation permission entirely, and
no processor-dependent kind is asserted anywhere.

One facet was correctly left **unimplementable**. 10.1.4 p5 permits pure
elemental function elements to be evaluated in arbitrary order or
simultaneously, so `pure-element-order-latitude` cannot have an oracle — and a
function with side effects is not a legitimate detector. The reviewer was
required to audit that claim in **both** directions, since an over-broad
unobservability claim is itself a defect, and confirmed it was not used as cover:
the observable value and shape facts were implemented, and the
conditional-expression facets remain genuinely pending rather than suppressed.

**The batch121 lesson held exactly as predicted.** After the 14 fixture reviews
were recorded, the audit reported 10.1.4 as non-reviewed — binding facets
changes catalogue content and stales its content-bound source review by design.
It was renewed in the same integration, recording that the staleness is
attributable *solely* to binding and that the source accounting is unchanged.
That rule is now doing its job automatically rather than being discovered by a
failing gate.

Two things are worth recording about process. An integrator-raised discrepancy —
the author reporting `shape = [2,3]` alongside only three values, which looks
wrong for a six-element section — was referred to the reviewer rather than
assumed benign; it resolved cleanly, with all six values deriving and three
asserted as representatives. Separately, the author **misreported its own
counts** (claiming `authored_facets` 2537→2551 and 1856 reference-validated).
The true movement is **1,839 → 1,853** and **1,821 → 1,835**, measured directly
from the worktree. The reviewer was given the correct figures so the error could
not propagate into the receipt or this log.

What this does **not** establish: no evaluation order, no evaluation count, and
no claim that any particular operand *was* evaluated. Passing under two
compilers is corroboration, never proof of universal conformance.
See `doc/source_audits/batch_126.json`.

## Batch 127 — operation classification, and a vacuity a mutation campaign missed

Establishes **13 facets** of **10.1.5.1 Intrinsic operation classification**:
unary plus, the five numeric operators, two character concatenation facets, and
the five logical operators.

The review of this packet produced the most instructive finding of the
checkpoint, and it is worth recording in full because it changes how fixtures
must be tested from here on.

**The logical truth tables were vacuous.** `.AND.` asserted only `(T,T)->T` and
`(T,F)->F` — rows on which **`.EQV.` behaves identically**. `.EQV.` was
correspondingly indistinguishable from `.AND.`, and `.OR.`, tested only on
`(F,F)->F` and `(F,T)->T`, was indistinguishable from `.NEQV.`.

The reviewer did not infer this from reading the code. It **substituted the
wrong operator into the source** — `.AND.`→`.EQV.`, `.EQV.`→`.AND.`,
`.OR.`→`.NEQV.` — and all three tests **still passed under both compilers**. A
test that passes when the feature under test is replaced by a different feature
establishes nothing at all.

The part that matters for the project: **this survived a 114-mutation campaign
that the author reported as fully passing.** Those mutations corrupted oracles,
inputs and observations — and a wrong-operator implementation survives every one
of them, because the oracle and the operator are wrong together in a consistent
way. Only mutating the **feature under test** can expose it.

That yields a new standing precedent, now recorded in `plan.md`:

> For any packet testing an **operator** or a **classification**, the mutation
> campaign must include **substituting every plausible alternative operator**.
> An oracle/input/omission sweep is provably insufficient.

The correction asserts the **full `TT`/`TF`/`FT`/`FF` table** for all four binary
operators, with an explicit row-by-row argument that each table is inconsistent
with each of the other three, and completes `.NOT.` to both rows. The reviewer
then re-ran **all twelve** operator substitutions rather than the sample it was
asked for: **24 of 24 compiler runs failed**, as required. The twelve
substitutions are now **permanent in the generator**, so the defect class cannot
silently return.

On what these fixtures honestly establish: classification is a **static,
source-level** property, and no running program can print that an operation was
classified as numeric. Every fixture here observes a runtime *consequence* — a
value, a `LEN`, a `KIND`, a branch result. The reviewer examined the catalogue's
recorded limitation on exactly this point and judged it **specific and honest
rather than boilerplate**. The strongest oracle in the packet is `17/5 = 3`,
which genuinely discriminates integer truncation from real division; the weakest
is unary plus, which is near-identity and supports value preservation only — it
was retained with its limitation recorded rather than overclaimed.

The restriction analysis was confirmed sound in **both** directions: 10.1.5.1 p6
contains only one explicit `shall`, the `character-kind-match-restriction`
deferral is correct because distinct character kinds are processor dependent,
and **no required diagnostic was wrongly deferred**. Only the character result
kind is asserted, respecting the 10.1.9.3 p4 precedent that for equal-range
integer, equal-precision real or different-kind logical operands only *one of
the operand kinds* is required.

One process point was settled here. A sibling reviewer raised the post-binding
**stale catalogue review** as a defect against its author. That was
**overruled**: authors are explicitly barred from running any `--record-*`
operation, so a stale review is the *correct* intermediate state, and renewing
it is integrator work done at integration — as it was here for 10.1.5.1.
See `doc/source_audits/batch_127.json`.

## Batch 125 — relational operations, and a systemic defect confirmed

Establishes **12 facets** of **10.1.5.5.1 Relational intrinsic operation
interpretation** across 11 fixtures: the two-operand comparison, all six
dotted/symbolic spelling pairs, and all five character equality and
blank-padding facets. It took **three review rounds**.

The blank-padding work was right from the start and the reviewer confirmed it
against p8 independently: the **shorter** operand is extended on the right with
blanks to the length of the longer, so `'A'` against `'A  B'` pads to `'A   '`
and differs at position 4 — blank versus `B`. The **zero-length equality** case
is stated **explicitly** in p8, so it is source-supported rather than assumed.
No collation-order oracle was needed for any of it.

Two findings blocked the packet, and one was overruled.

**C1055FR-001** caught a vacuous oracle: `KIND(observed) - KIND(.FALSE.) == 0`,
where `observed` is declared `LOGICAL` with no kind selector. Its kind is
default **by declaration**, so the assertion observed the *variable* and never
the kind of `left < right` — it would pass even if the relational operation
produced a non-default logical result, because the assignment would convert it.
The author was offered either a direct expression oracle or withdrawal, and
chose **withdrawal to pending**. That was the right call: kinds are processor
dependent, so a load-bearing non-default-kind mutation may not be portably
constructible here, and a smaller honest packet beats a larger one carrying a
dead assertion.

**C1055FR-004** is the one that matters for the project. Applying the
wrong-operator substitution technique that had just blocked the sibling 10.1.5.1
packet, the reviewer found **four surviving mutants**: `<`→`<=`, `.LT.`→`.LE.`,
`==`→`<=`, and `/=`→`>` all **passed** on both toolchains. The 179-mutation
oracle/input/omission campaign could not possibly have caught them.

The root cause is worth stating precisely, because it generalises: **the chosen
operands never exercised the rows where the operators differ.** `<` and `<=`
differ *only* on equality; `==` and `<=` differ only when the left operand is
less than the right; `/=` and `>` likewise. Operands of `(-4,3)`, `(3,-4)`,
`(7,7)` and `(7,-2)` simply never land on those rows.

The fix is a **design rather than a patch**. All six pairs now assert the same
three rows — less `(-4,3)`, equal `(5,5)`, greater `(8,1)` — which yield six
truth-signatures: `TFF`, `TTF`, `FFT`, `FTT`, `FTF`, `TFT`. All six are
**distinct**, so three rows uniquely determine every operator. That discrimination
was verified independently at integration and has no collisions. Sixty
substitutions (30 operator/alternative pairs across both spellings) are now
**permanent in the generator**, and the reviewer re-ran **all** of them:
**120 of 120 compiler runs failed** as required.

**C1055FR-002 was overruled.** The reviewer flagged the post-binding stale
catalogue review as a packet defect. It is not: binding facets stales a
content-bound source review *by design*, authors are explicitly barred from
running any `--record-*` command, and renewal is integrator work done at
integration — as it was here.

The headline for the project is not this packet but the pattern. **Two of the
three fixture packets in this checkpoint shipped wrong-operator vacuity**, one of
them surviving a 114-mutation campaign. That makes it systemic to fixture work
rather than an individual lapse, and it is now a standing rule: for any packet
testing an operator or a classification, build the discrimination table *before*
writing code, and bake the substitutions into the generator permanently.
See `doc/source_audits/batch_125.json`.

## Batch 130 — array constructors, and a near-miss on false validation

Establishes **7 facets** of **7.8 Array constructors** across 4 fixtures, and is
the **first fixture packet this session accepted with no defects at all**.

The reviewer did the derivation work properly rather than taking the author's
word. It followed the conversion **delegation chain** itself — 7.8 p3 delegates
explicit type-spec conversion to intrinsic assignment, and 10.2.1.3 p11 requires
right truncation and blank padding — confirming that
`[CHARACTER(3)::'A','BCDE']` yields `'A  '` and `'BCD'`, with the longer operand
**truncated**. It confirmed the **empty array contributes zero elements**, so
`[one,empty,three]` has extent 4 rather than 5; that was the claim most likely
to be subtly wrong. And it confirmed from 19.4 that the `ac-do` index is a
**separate statement entity**, so the host `i` correctly remains 99.

Non-vacuity here rests on the mutation classes that actually matter for a
constructor: **reorder, drop and duplicate**. An oracle that sums, sorts, or
uses `ANY`/`ALL` checks only the *multiset* of values and would survive all
three — and sequence is the entire point of a constructor. The reviewer re-ran
them, including mutating the empty array to contain one element, which is what
genuinely proves "empty contributes nothing". No `RESHAPE`, `PACK`, `SPREAD`,
`MERGE` or `TRANSFER` is used as an oracle; elements are read back **by
subscript** against hand-computed literals.

Polymorphic constructors were left pending after a probe reproduced a **gfortran
16.1 internal compiler error**, with LFortran also rejecting via ASR
verification failure. A reference-compiler ICE is not grounds to weaken or
fabricate a test, and it is not automatically a defect in either compiler or the
standard. It is recorded as worth a future upstream report.

### The integration lesson — a near-miss worth recording

Binding into 7.8 **staled five pre-existing fixture reviews**. This is a broader
form of the batch121 rule: the Clause 10 catalogues in the previous checkpoint
had *no* existing fixtures, so renewing the catalogue review was sufficient
there. 7.8 already had fixtures bound to it, and their **own** reviews went
stale too.

The near-miss: four of the five **refused** to renew as `reference-validated`,
erroring with *"no successful reference at the required phase and supported
mode"*. Investigation showed they had always been **`source-reviewed`**, not
reference-validated, and do not pass under gfortran in that mode — which is
exactly why `source-reviewed` had dropped from 274 to 270. Had the renewal been
forced through at the wrong state, the suite would have recorded a **false
reference validation** for four cases. They were renewed at their **original**
state, and the count returned to 274.

The rule is now explicit: a fixture packet must renew **the catalogue source
review for every catalogue it binds into**, *and* **every pre-existing fixture
review in those catalogues** — each at its **own original review state, never
upgraded**.

Two further records came out of the same investigation. The execution aggregate
`S4.2-001.whole-suite-execution` was stale; bisection showed it went stale at
**batches 122–124**, when Clause 11 source registration changed the source
inventory it binds to, and it has been renewed here as an observational
inventory renewal claiming no new execution or facet completion. Separately,
**13 of 22 evidence links are stale and were already stale at `df0feaf`**,
predating this work entirely. They were deliberately **not** renewed in bulk:
`--record-evidence-review` independently adjudicates a link *after* source and
fixture review, so approving thirteen in a single integrator pass would be
precisely the unearned approval this protocol exists to prevent. They are
recorded as the `stale-evidence-link-adjudication` followup.
See `doc/source_audits/batch_130.json`.

## Batch 128 — ALLOCATE execution, and three real compiler defects

Establishes **13 facets** of **9.7.1.2 Execution of an ALLOCATE statement**
across 10 fixtures, and produces the **first XFAILs since batch120**: three
genuine defects in the frozen LFortran, each verified against the pinned
standard *before* any XFAIL was contemplated.

**Defect 1 — `SOURCE=`/`MOLD=` shaped allocation is rejected.** R930 defines
both specifiers and C943 permits *no* explicit bounds when `source-expr`
appears with the same rank; 9.7.1.2 p7 then requires the array to be allocated
"with the shape of source-expr, and with each lower bound equal to the
corresponding element of `LBOUND(source-expr)`". The frozen LFortran instead
emits *"Allocate for arrays should have dimensions specified"* — an ASR
verification failure in one case and a semantic error in the other. gfortran
accepts both.

**Defect 2 — the `SOURCE=` expression is evaluated more than once.** This one
deserved scepticism and got it. The project already holds that **evaluation
counts are generally not observable**, and "evaluated once" claims are exactly
the sort of thing that turns out to be processor latitude — in which case the
*fixture* would have been invalid and withdrawn, rather than LFortran earning
an XFAIL. I put that challenge to the reviewer explicitly, and it settled the
question by quoting 9.7.1.2 p8 verbatim: *"The source-expr is evaluated exactly
once for each execution of an ALLOCATE statement."* An explicit requirement,
not a latitude. The frozen target evaluates it twice.

The reviewer also confirmed the packet's highest-risk oracle. `SOURCE=s` with
`s(-3:-1,5:8)` gives the allocated object lower bounds `[-3,5]`, **not** unit
lower bounds with the same shape — the rule most easily got backwards, and the
fixture has it right.

On non-vacuity, the reviewer re-ran **all 273** generated mutations rather than
a sample: 273 of 273 killed, including all 11 feature-level ones. Two
discipline points carried this packet:

- **Every fixture asserts `LBOUND` *and* `UBOUND`, not merely `SIZE`.** A
  processor that allocated the wrong bounds would sail through an
  `ALLOCATED(a)` check, and would survive a `SIZE`-only check for any shape
  with the same extent.
- **No payload sentinel is `0`.** Freshly allocated memory is frequently zero,
  so a zero payload proves nothing about what was written. Zero appears only
  where the standard requires it — `STAT=0`, `SIZE=0` — and in counters.

The observability limits held: no `TRANSFER`, `LOC` or address-based oracle; no
undefined value or association status is ever read (the `MOLD=` fixture reads
only its own fresh writes); no `ERRMSG` text oracle; and **no resource-exhaustion
`STAT=` test**, since deliberately failing an allocation by requesting a huge
array is not portable.

The XFAIL sequence was followed strictly and as separate operations: full suite
gate (**1010 tests OK**), then `--record-execution-review`, then
`--update-xfail`. The baseline moved **807 → 810** — exactly three additions,
zero modifications to existing lines. I reproduced the frozen-target result
myself first, observing precisely 3 FAIL / 7 PASS.

These three cases are not evidence of conformance under the frozen toolchain.
They are evidence of defects in it.
See `doc/source_audits/batch_128.json`.

## Batch 129 — initialization, where zero is the enemy

Establishes **10 facets** of **8.4 Initialization** across 10 fixtures, and adds
two more verified frozen-LFortran defects.

This section has a uniquely dangerous vacuity mode, and it is worth stating
plainly because it is counter-intuitive: **uninitialized memory is very often
already zero, and many compilers zero-fill.** A test asserting `x == 0` after
`INTEGER :: x = 0` therefore proves **nothing** — it passes identically on a
processor that ignores initialization entirely. The same applies to `.FALSE.`
and to blank strings.

The packet was required to use only distinctive non-default sentinels, and the
reviewer audited a **full sentinel table**, recording for each fixture what an
initialization-ignoring processor would produce instead and which guard rejects
it: `-31417`, `.TRUE.`, `2719`, `'Zq7R'`, `'Bx'`, `-24681`, `13579`, `[2,3,5]`,
`-22231`, `-27182`, `-12345`. For the character cases it noted the right
subtlety — it is the **nonblank prefix** plus the explicit `LEN` assertion that
carries the case, not the blanks themselves.

The decisive feature-level mutation here is **removing the initializer**, and
the reviewer re-ran that across a scalar, an array constructor, a character
truncation, a `DATA` statement and a pointer target. All failed as required, so
no fixture passes with initialization absent.

Two **deliberate exclusions** were audited rather than accepted, on the
principle that an over-broad unobservability claim is itself a defect. Both
stand: a `.FALSE.` initializer is vacuous under zero or default fill, and a
length-zero character initializer leaves no payload to observe.

**Defect 1 — initial pointer target rejected.** 8.2 R805 permits
`=> initial-data-target`, 7.5.4.6 C770 requires the target be a nonallocatable,
noncoindexed variable with `TARGET` and `SAVE`, and 8.4 p2 says the object is
then initially associated with it. The fixture's target satisfies every one of
those conditions, yet the frozen LFortran rejects with *"Initialization of `p`
must reduce to a compile time constant"*. gfortran accepts.

**Defect 2 — `DATA`-part `SAVE` retention fails.** The reviewer was warned that
*"a variable in a `DATA` statement"*, *"initialization implies `SAVE`"*, and
*"retention across calls"* are three **distinct** claims, and it established the
chain through all three rather than asserting the conclusion: 8.6.7 p1 makes a
`DATA` statement explicit initialization; 8.6.7 p4 gives a named variable the
`SAVE` attribute if **any part** of it is initialized in a `DATA` statement; and
8.5.16 p1 requires the value be retained after `RETURN`/`END`. So
`data a(-2) /-12345/` saves the **whole** array, and the updated values must
survive the second call. The frozen LFortran compiles but fails at runtime.

One derivation is worth recording for reuse: the kind-conversion fixture uses
`selected_int_kind(18)`, which is **portable** because 7.4.3.1 p2 requires an
integer representation range of at least 18. That avoids the usual trap of
assuming a particular numeric kind code exists.

The XFAIL sequence was again run as separate operations, moving the baseline
**810 → 812** with exactly two additions and no modifications. I reproduced the
frozen-target result independently: 2 FAIL, 8 PASS.
See `doc/source_audits/batch_129.json`.

## Batch 133 — structure components, and a shape rule worth getting right

Establishes **12 facets** of **9.4.2 Structure components** across 12 fixtures,
and adds one more verified frozen-LFortran defect.

Everything here turns on the **rank and shape derivation**, and the reviewer
derived it from source rather than checking the author's chain:

- **9.4.2 p2** — a part-ref's rank is the rank of the part name, or, with a
  section subscript list, "the sum of the number of subscript triplets, the
  number of vector subscripts, and the sizes of one of the arrays in each
  multiple section subscript".
- **C919** — "There shall not be more than one part-ref with nonzero rank."
- **9.4.2 p3** — the data-ref's rank is that of the single nonzero-rank part-ref.

Together these make `array_parent%array_component` invalid, which is the rule
that makes this section subtle.

The worked case is `x(2:6:2)%alpha`. The triplet selects 2, 4 and 6 by
9.5.3.4.2 p3, giving extent 3; 9.5.3.4.1 p2 takes the shape from the
nonzero-rank part-ref; and **16.9.119 p5 fixes `LBOUND` at 1** rather than
inheriting the parent's lower bound. Required: `SHAPE=[3]`, `LBOUND=[1]`,
`UBOUND=[3]`. That last detail is precisely the sort of thing a plausible
implementation gets backwards — and the **frozen LFortran does get it wrong**,
failing with `SC:rank_from_nonzero_part_ref:shape`. gfortran passes 12/12. The
case is XFAILed with the required result hand-derived from the standard, not
inferred from gfortran's agreement.

On non-vacuity, the decisive mutations for this section are **changing which
component is referenced** and **changing the parent subscript**: 24/24 and 13/13
respectively, within 371/371 overall, and the reviewer re-ran 52 of its own.
The enabling design choice deserves recording, because it is easy to omit:
**every component and every array element carries a distinct value.** Without
that, both mutation classes would be **invisible** — swapping `x%a` for `x%b`
changes nothing observable if both hold the same number.

Two items were recorded rather than blocked. The `component-value-swap`
mutations mostly swap **common control values** rather than each fixture's
primary feature values, so those category counts overstate what they exercise;
the reviewer ran feature-local swaps of its own and all failed, so the fixtures
are genuinely sensitive and only the labelling is imprecise. And the
multiple-section-subscript facet is deferred because **both** toolchains reject
the F2023 `@` syntax — gfortran with "Expected array subscript", LFortran's
tokenizer not recognising `@` at all. No non-`@` alternative demonstrates it,
and a toolchain limitation is not grounds to fabricate a test.

The seven remaining pointer and subobject facets were explicitly left as
implementable future work rather than claimed impossible — an over-broad
unobservability claim would itself be a defect.
See `doc/source_audits/batch_133.json`.

## Batch 132 — deallocation, and fixtures the gate never ran

Establishes **11 facets** of **9.7.3.2 Deallocation of allocatable variables**,
and adds three more verified frozen-LFortran defects. It was **blocked** on a
defect that had nothing to do with the tests themselves.

**The fixtures were invisible to the unittest gate.** `run_tests.py` collected
them, but the gate discovered **1016 tests — identical to the base** — with zero
deallocation test methods, because the packet shipped **no generator and no test
module**. That also meant `--check` did not exist and the claimed mutation
campaign was **not reproducible from the committed tree**.

I caught this before the review ran, from a single number: the packet reported a
full suite of 1016, exactly the base, despite adding 11 cases — while a sibling
packet adding 12 cases moved 1016 → **1021**. A fixture the gate never executes
cannot regress, cannot be trusted, and silently contributes nothing. The
correction added both files; regeneration is **byte-identical**, the suite rose
to 1021, and the reviewer re-ran the feature-level mutations **through the
generator** (12/12 fail, 11/11 reverse controls pass) rather than by hand, which
was the entire point.

That yields a standing check, now in `plan.md`: **a fixture packet must ship a
generator with `--check` and a test module, and the full-suite count must rise.**
An unchanged count means the cases are inert.

On the tests themselves, this section has a hazard that makes it unusually easy
to write something meaningless. **After deallocation the value is gone and the
contents are not observable** — reading deallocated storage is undefined
behaviour — and a pointer whose target was deallocated has **undefined
association status**, so `ASSOCIATED()` on it is not a legitimate oracle. The
reviewer checked all 11 sources line by line and found no such read.

The subtler point is that **`ALLOCATED(x) == .false.` is a weak oracle on its
own**: a processor that never allocated at all also reports false, and `.false.`
is default-equivalent, so a zero-filled logical satisfies it. Every fixture
therefore proves the **positive** state — allocated, with bounds and values —
*before* deallocating, using non-unit and negative lower bounds so a wrong-bounds
reallocation is detectable.

Three defects were confirmed, all normatively grounded:

- **9.7.3.2 p1 with 9.7.4 p5** — deallocating an unallocated allocatable "causes
  an error condition", requiring a **positive** `STAT` distinct from the image
  codes. Only portable properties are asserted; no processor-dependent value and
  no resource-exhaustion path.
- **8.5.16 p1** — `SAVE` retains "association status, allocation status,
  definition status, and value".
- **9.7.3.2 p8 with 7.5.6.3 p2** — derived-type deallocation deallocates
  allocated allocatable subobjects and finalizes them.

The `SAVE` one deserved the scrutiny it got. The author cited *"NOTE 1/SAVE
control"* — and **notes are not normative**. Had a note been the only support,
the *fixture* would have been unfounded and LFortran's behaviour unremarkable,
making it a test defect rather than a compiler defect. The reviewer found the
normative sentence in 8.5.16 p1, so the claim stands. That distinction is the
difference between reporting a real bug and manufacturing one.

Baseline **813 → 816**, three additions, no modifications.
See `doc/source_audits/batch_132.json`.

## Batch 131 — structure constructors, and proving a crash is a defect

Establishes **15 facets** of **7.5.10 Structure constructors**, and adds three
more verified frozen-LFortran defects — one SIGSEGV and two compile-time ICEs.

The interesting part of this packet was not writing it but **adjudicating the
crashes**. Two of the three suspected defects depended entirely on one question:
**is intrinsic `NULL()` valid for an *allocatable* component?**

The question matters because the rules differ by component kind — for a
**pointer** component `NULL()` plainly gives disassociated status — and it is
easy to assume the allocatable case by analogy. If `NULL()` were *not* permitted
there, the fixtures would have been **invalid**, LFortran's rejection would have
been **correct**, and this would have been a blocking test defect rather than two
compiler defects. An ICE and a SIGSEGV are **crashes, not diagnoses**; a compiler
falling over tells you nothing about whether the program conforms. So the source
had to be proven conforming first.

It is: **7.5.10 p6 explicitly permits** intrinsic `NULL` for allocatable
constructor expressions and states the component "has a status of unallocated",
and `NULL(MOLD=...)` is valid via 16.9.155 p3/p4/p7. The fixtures are conforming
and all three crashes are genuine defects.

Two derivations were checked independently and both were right. The
**conforming-array bound mapping** — `source(1:3)` maps to component
`values(-1:1)`, so the component keeps its **declared** bounds rather than
inheriting the source's — is exactly the detail that gets got backwards. And the
numeric conversion uses `4.0`, which is **exactly representable**, so no rounding
ambiguity arises under 7.4.3's approximation rule.

The decisive non-vacuity check for this section is that **removing the omitted
defaults makes the test fail**. A default-initialization fixture whose default is
a zero-equivalent value would pass on a processor that ignores default
initialization entirely; defaults `(11,13)` with override `(11,29)` are
non-default-equivalent, so the check bites.

Related care was taken with the **status-only oracles**. `omitted-allocatable-status`,
`known-disassociated-pointer` and the two `NULL()` cases all assert *unallocated*
or *disassociated* — both **default-equivalent** states that a processor which
never allocated would also report. Each was confirmed to read **no bounds or
values**, so no undefined state is observed, and to establish a real contrast
rather than resting on the default state alone.

Infrastructure was checked explicitly this time, because a sibling packet in the
same checkpoint was blocked for shipping fixtures with neither a generator nor a
test module: this packet has both, regeneration is byte-identical, and the suite
count genuinely rose.

Baseline **816 → 819**, three additions, no modifications.
See `doc/source_audits/batch_131.json`.

## Batch 136 — opening Clause 13, and why corrections get re-verified

This is the first source packet since Clause 11 closed at batch124, and it
**opens Clause 13**, previously entirely unregistered. It registers **13.1,
13.2.1, 13.2.2, 13.3.1, 13.3.2, 13.3.3 and 13.4** — 66 base units over PDF
pages 289–294, in seven catalogues with 58 requirements and 172 pending facets.

The stakes are higher than the unit count suggests: **these registrations are
the specification every future format and edit-descriptor fixture will execute
from**. An error here does not stay local; it propagates into downstream tests
that look authoritative.

It took **three rounds and seven blocking findings**.

The count report was **internally inconsistent** — a claimed delta of 66, equal
to *all* base units in scope, alongside a separate claim of 35 already-counted
and only 31 newly-accounted. Measuring `main` directly before dispatching the
review showed 2363, not the reported 2326. The true movement is **2363 → 2392,
net +29**: 31 non-numbered units newly classified, offset by two numbered
deferrals. The catalogue content was right throughout; only the arithmetic in
the report was wrong.

Those two deferrals were the packet's best instinct. `R1303` and `C1302` already
have legacy fixtures, and registering a numbered rule that has pre-existing
cases **structurally forces binding them** — the trap that blocked batch113.
Both were left `unresolved` but **fully accounted**, with a migration followup.

The anticipated **table hazard did not materialise**: PyMuPDF detection found
**zero tables** on pages 289–294 — Clause 13's tables live in later sections. So
the real risk was the dense **grammar alternative lists** in `R1307`, `R1313`,
`R1315` and `R1317`–`R1322`, which were checked alternative-by-alternative by
both author and reviewer, since every future format fixture derives from them.

Four findings concerned the substance. 13.4 p9 was under-specified, missing the
nested-group reversion target, the no-preceding-parenthesis fallback, the
DT-parenthesis exclusion, and the changeable-modes obligation. **13.2.2 p2 was
dispositioned `permission` despite carrying mandatory `shall` text** — the third
occurrence of that defect class, after 11.7.2 and 11.7.5 in batch123; latitude is
a permission, never a requirement, and the check runs in both directions.
`C1309` omitted `m`, `d` and `e`, three fields that could have gone untested
indefinitely. And the **pending plans were placeholders** — "expected records
must be fixed before execution" — rather than byte-exact specifications, which
matters because format output is byte-exactly testable through an internal
`WRITE` to a character variable with **no file I/O at all**.

### The part worth remembering

**Two of the seven findings were defects the first correction itself
introduced**, and were caught only on re-verification.

One new plan expected `'(SP,*(I2))'` with values 7 and 8 to produce two
records — **assuming record advancement that Note 4 explicitly denies**: "There
is no file positioning implied by unlimited-format-item reversion." That
contrast with p9's slash-like positioning is the entire reason p8 and p9 carry
separate facets, so inverting it would have produced a confidently wrong fixture.

The other used `("X")` with an I/O item as a negative — which violates **both**
p2 and p9, so a processor rejecting it might be enforcing p2 and say nothing
about the reused-portion rule. Every negative must be attributable to the
**single** rule it is filed under. The replacement, `'(I1,("X"))'`, satisfies p2
via the leading `I1` while the reversion target `("X")` lacks a data descriptor,
violating p9 alone.

The reviewer hand-verified all four exact record specifications against the
source, including that `("H",2(I1))` genuinely reuses the repeat count and that
`("H",I1)` falls back to the first left parenthesis without re-emitting `H`.

Source accounting only: `authored_facets` unchanged at **1,946**, no fixture
bound, no compiler invoked, `tests/` diff empty. 13.5–13.11 remain unregistered,
as does **Clause 12**, the immediate I/O-statement neighbour.
See `doc/source_audits/batch_136.json`.

## Batch 134 — logical interpretation, on the material that blocked batch127

Establishes **21 facets** of **10.1.5.4.1 Logical intrinsic operation
interpretation** across 6 cases, accepted with **no findings**.

This packet sat on exactly the material that produced the worst defect of the
session. Batch127 tested 10.1.5.1's logical operators and shipped **vacuous
truth tables**: `.AND.` was asserted only on rows where `.EQV.` behaves
identically, so substituting the wrong operator into the source left the tests
**passing under both compilers**. It had survived a **114-mutation** campaign,
because when the operator under test is wrong, the oracle is wrong *with* it,
consistently — oracle and input mutations cannot see it.

So confirming non-recurrence was the review's first job. Here the full
`TT/TF/FT/FF` set is asserted **directly in the emitted sources** for every
binary operator, matching Table 10.6, and each table is therefore inconsistent
with all three alternatives. The separating rows are precisely the ones batch127
omitted: **`.AND.` and `.EQV.` differ only at `FF`; `.OR.` and `.NEQV.` only at
`TT`.** The reviewer re-ran **all twelve** operator substitutions on both
toolchains — 24 of 24 compiled and then failed, zero unexpected passes —
including the three that previously survived. Those substitutions are now
**permanent generator data**, which is what stops the class returning rather
than fixing one instance of it.

The second thing worth flagging is the **binding density**: 21 facets from only
6 cases, or 3.5 per case, against 15/15 in batch131 and 12/12 in batch133. Dense
binding is not wrong — one program can legitimately establish several related
facts — but it is exactly how a weak facet hides behind a strong one. The
reviewer audited it facet by facet and found no over-binding: each facet is
separately observable in the case it is bound to.

One oracle detail was checked specifically against a past failure. The
result-type checks observe the **expression** directly, passing `.eqv.` and
`.not.` expressions to `logical` dummy arguments with no intermediate variable.
That matters because batch125 shipped `KIND(observed) - KIND(.FALSE.) == 0`
where `observed` was declared default-kind — measuring the *declaration* rather
than the expression — and that facet had to be withdrawn. No result-kind claim
is made here at all, which respects 10.1.9.3 p4: for different-kind logical
operands only "one of the operand kinds" is required, so a specific result kind
is generally not assertable.

The disclaimers were checked in **both** directions. The packet establishes
nothing about short-circuiting or evaluation order — a processor need not
evaluate all of an expression if the value can be determined otherwise — and the
reviewer confirmed both that no such claim sneaks in and that the disclaimer is
not **too broad**, since an over-broad unobservability claim is itself a defect.

Only `operand-type-delegation` remains pending, correctly: p1 delegates operand
admissibility to 10.1.5.1.
See `doc/source_audits/batch_134.json`.

## Batch 135 — CONTIGUOUS, where almost nothing is observable

Establishes **10 facets** of **8.5.7 the CONTIGUOUS attribute**, accepted with
no blocking findings.

This section is unusual in that its subject matter is largely **outside what the
suite can observe at all**. `CONTIGUOUS` is about storage layout, and the project
holds that layout, addresses and allocation mechanism are not observable — no
`TRANSFER`, no `LOC`, no address or timing oracle. The only legitimate instrument
is `IS_CONTIGUOUS`.

But `IS_CONTIGUOUS` is a valid oracle **only where the standard requires a
result**. Where the standard merely *permits* a processor to lay something out
contiguously, asserting **either** value would be wrong, because a conforming
processor could report either. That distinction is the whole packet, so the
reviewer traced every one of the ten facets to a **specific numbered clause**:

- 8.5.7 **p2(1)** an object with the CONTIGUOUS attribute
- **p2(2)** a nonpointer whole array that is not assumed-shape
- **p2(3)** an assumed-shape array argument associated with a contiguous array
- **p2(5)** an array allocated by an `ALLOCATE` statement
- **p2(6)** a pointer associated with a contiguous target
- **p2(7)** the nonzero-sized section conjunction — contiguous base, no vector
  subscript, same element order, excluded elements only preceding or following,
  and for character arrays a substring-range specifying *all* characters of the
  parent string
- **p3** for the two negatives

with 16.9.115 p5 supplying the oracle semantics. None rests on latitude.

The second issue is subtler and easy to miss: **`.FALSE.` is a
default-equivalent value.** A zero-filled logical reads false, so a negative
facet asserting `IS_CONTIGUOUS` is `.FALSE.` would also pass on a program that
never established the property at all. Both negatives therefore carry
**same-program `.TRUE.` controls**, and the reviewer confirmed those controls
genuinely execute before completion, so each program demonstrably distinguishes
the two states.

Non-vacuity rests on **designator mutation** — changing the designator so it is
no longer contiguous — with 10/10 failing on both compilers inside a 262-run
matrix, three of which the reviewer re-ran itself along with a reverse mutation.
`LEN(c(2:4)(1:4)) == 4` is asserted explicitly for the character substring case,
guarding the blank-padding trap.

Sixteen facets remain pending, and the deferral was checked rather than assumed:
layout, padding, copy strategy and timing are genuinely unobservable, and the
`S8.5.7-002` restriction facets lack a **required portable diagnostic**, so they
cannot carry a diagnostic expectation. Nothing `IS_CONTIGUOUS` could legitimately
settle was left on the table.

What this does **not** establish deserves stating plainly, because the section
invites overreading: it establishes only the standard-required `IS_CONTIGUOUS`
result, plus bounds, shape and values. It says nothing whatever about actual
memory layout, addresses, padding, copy strategy, allocation mechanism or
performance.

One unrelated pre-existing failure surfaced during integration —
`S8_5_7_001_valid__contiguous_dummy_effect_assumed_rank` reports a gfortran
runtime failure. It lies outside this packet's scope, which covers only
`S8.5.7-003` and `-004`, was not introduced here, and is recorded rather than
silently absorbed.
See `doc/source_audits/batch_135.json`.

## Batch 139 — list-directed and namelist, and one error in mirror image

Registers **13.10.1–13.11.4.3** — 77 base units over PDF pages 308–316, in
sixteen catalogues, all newly accounted.

The whole packet turns on a single judgement: **which parts of list-directed and
namelist formatting are required, and which are processor dependent.** Output
form is largely latitude — field widths, separator spelling, record wrapping and
value representation are frequently not fixed — while the **input** rules for
separators, repeat counts, null values, slash termination and name matching are
tightly specified and genuinely assertable.

The two blocking findings are **the same error in mirror image**, which is
exactly why the check has to run in both directions.

**C139SR-001 claimed latitude where a requirement exists.** The F/E choice for
real output was marked *wholly* processor dependent — but 13.10.4 p5 fixes one
case: a real **zero must use F form**. The claim was too broad, and **an
over-broad unobservability claim is itself a defect**. Marking a whole unit
unassertable because *most* of it is latitude silently discards the part that is
required, and nothing downstream ever revisits it. The rule propagates to
namelist output through 13.11.4.2 p1.

**C139SR-002 ran the other way, claiming a requirement where latitude exists.**
A plan asserted the exact substring `'I='` while the same packet marked spacing
around the equals sign processor dependent. 13.11.4.3 p2 says the name is
*followed by* an equals sign — **not** "immediately followed" — so a conforming
processor may emit `I =`. An exact-string plan that a conforming processor can
fail is **worse than no plan**: it becomes a fixture that fails on correct
compilers.

The correction for the first was written carefully enough not to become the
second. The new `real-zero-uses-F-form` facet asserts **only the form** — that
no E-form exponent marker appears — and explicitly **not** the width, digit
count, sign, decimal spelling or separators. Over-asserting there would have
replaced one defect with its mirror.

Four fixed forms survive and were hand-verified **including their leading
blanks**: `' T'` and `' F'` from 13.10.4 p3 with p13, `' AB'` for delimiter mode
`NONE` from p8, and the namelist prefix `' &G'` from 13.11.4.3 p3 and p5. The
reviewer specifically checked that relaxing the equals-spacing claim had not
discarded the genuine obligations around it.

Three verifications are worth recording because each was a claim that could have
hidden an error. **Zero numbered R or C units across all 77** — unusual enough to
demand checking, since batch136 found nineteen in 13.1–13.4 and a sibling found
`R1323`; confirmed, with `R901` appearing only as a cross-reference. **13.10.4
contains no table** despite being the flagged candidate as the densest remaining
block, with the two NOTE result tables re-read row-by-row. And the **four
sections sharing page 312** were re-partitioned unit by unit — a misattributed
paragraph would have been completely invisible in the totals, since 77 would
still have been 77.

Source accounting only: `authored_facets` unchanged at **1,977**, no fixture
bound, no compiler invoked. Clause 12 remains unregistered, and namelist leans
on it for internal-file, `NML`, `DELIM` and `DECIMAL` mechanics.
See `doc/source_audits/batch_139.json`.

## Batches 137 and 138 — Clause 13 complete at 283/283

These two packets, with batch139, **complete Clause 13** — 283 of 283 base units
across 58 sections. It is the **sixth source-complete clause**, after 6, 8, 9,
10 and 11.

### Batch 137 — data edit descriptors, and where the tables live

Registers **13.5 through 13.7.2.4** — 76 base units over PDF pages 294–303,
covering integer, F, E/D, EN, ES, EX, complex, rounding and BOZ editing. Only
one numbered item appears in the whole scope, `R1323`.

batch136 found **no** tables in 13.1–13.4 and inferred they lived in the later
sections. That inference is now confirmed: **Tables 13.1, 13.2 and 13.3 are
here**, and PDF extraction **interleaved their columns**, so the author had to
reconstruct the rows. The reviewer read all three **row by row** against the PDF
independently. That matters more than it sounds — every future E/EN/ES fixture
derives from those rows, so a scrambled row becomes a confidently wrong test.

I found the first blocking defect myself, before the review completed. Two
sample plans gave a **negative** result for the **positive** input `0.5`:
`'-500.000E-03'` and `'  -5.000E-01'`. But `SS` suppresses the optional plus
sign, so for a positive value the sign position must be **blank** — the correct
values are `' 500.000E-03'` and `'   5.000E-01'`.

The principle is worth stating, because it inverts the earlier lesson: batch136
was blocked for plans that were too **vague**, and the natural overcorrection is
to write something precise. But **a precise-but-wrong plan is worse than a vague
one.** A vague plan stalls a future fixture author; a wrong one gets faithfully
implemented as a test asserting the wrong bytes, and then looks authoritative.

Two further findings followed. **Eleven units** mixing an obligation with a
grant of latitude were dispositioned wholly as `permission` — the **fourth**
occurrence of that class — and were re-dispositioned with the latitude confined
to rationale text; only 13.5 p3 remains a permission. And placeholder plans
still remained, so 48 entries were changed: 21 upgraded to exact executable
strings, 27 marked explicitly unassertable. There is no third state.

The reviewer independently derived the scale-factor pair, which is the nicest
check in the packet: `-1P,E10.3E2` gives `' 0.010E+02'` and `1P,E10.3E2` gives
`' 1.000E+00'` — both representing `1.0`, both fitting the same width and digit
count. It also confirmed the 27 unassertable markings are **genuine latitude**
rather than merely hard to compute, which is exactly the direction the sibling
13.10–13.11 packet got wrong.

`R1323` carries no diagnostic facet, correctly: its text is only
`hex-digit-string is hex-digit [ hex-digit ] ...`, which **defines a form and
prohibits nothing**.

### Batch 138 — control editing, and a defect class in mirror image

Registers **13.7.3 through 13.9** — 64 base units across **21 sections** over
eight pages, many crowded onto a shared page. That made **mis-partitioning** the
dominant risk: a paragraph attributed to a neighbouring subsection would be
completely invisible in the totals, since 64 would still be 64. The reviewer
re-partitioned p303, p304, p306 and p307 independently and confirmed the split,
including that **13.8.8 genuinely owns only p1** despite covering six
rounding-mode descriptors.

Four findings, each a distinct shape of error.

A negative was filed against **13.7.5.2.2**, which merely **cross-refers**:
*"Note that w cannot be zero for input editing"* is a reminder, and **"cannot"
is not "shall not"**. The real prohibition lives in 13.7.5.1 p1. Every negative
must be attributable to the single rule it is filed under.

Four units filed **latitude as requirements** — the **fifth** occurrence of the
mixed obligation/latitude class, and the exact **mirror** of its sibling
batch137, which filed **obligations as permission**. That symmetry is precisely
why the rule is bidirectional: a requirement misfiled as a permission is as
damaging as a permission inflated into a requirement. All four were split into
requirement and permission subunits.

An output-control facet sat under **13.9 p1**, which owns only the input
prohibition. And a negative named a descriptor but **no datum**, so nothing
demonstrated its branch was even reached. The fix, and the reviewer's
independent re-derivation, is the most intricate thing in the checkpoint: for
`(G4.1E3)` with datum **zero**, p5 gives `s=1` so the F branch is reached since
`0 ≤ s ≤ d=1`; `e=3` so `n = e+2 = 5`; therefore `w−n = 4−5 = −1`, violating p6.
The repair `(G7.1E3)` gives `w−n=2` and `d−s=0`, so `F2.0` emits `0.` with the
optional plus omitted under 13.7.2.1(5), followed by five blanks — exactly
`'0.     '`.

The **positioning trap** was specifically avoided. batch136's correction had
wrongly assumed record advancement where Note 4 denies it, and this scope *is*
position editing — `T`, `TL`, `TR`, `X`, slash — so every positioning plan was
checked against what the source actually requires, including that **skipped
positions are not necessarily blanked**.

### What completing Clause 13 does and does not mean

All 283 base units now carry a disposition and, where applicable, a requirement
with an explicit pending plan. **It is not test-complete**: Clause 13 has **zero
executable fixtures**. What it does unlock is the fixture seam — format output
is byte-exactly testable through an internal `WRITE` to a character variable,
with no files and no I/O units, and the plans now name exact expected characters
including blanks.
See `doc/source_audits/batch_137.json` and `doc/source_audits/batch_138.json`.

## Batch 140 — Clause 13's first executable tests

Clause 13 became source-complete at batch139 — 283 of 283 base units — with
**zero executable tests**, exactly the gap Clause 10 had before Checkpoint I.
This packet closes the first of it: **18 facets** of **13.7.2.2 integer
editing** and **13.7.2.4 B, O and Z editing**.

The registration work pays off directly here. The pending plans already named
the descriptor, the input value and the **exact expected characters including
blanks**, so the author was largely *executing* an independently reviewed
specification rather than inventing one.

What makes this clause unusually tractable is that **format output is
byte-exactly testable through an internal `WRITE` to a character variable** — no
files, no I/O units, no scratch directories. These are the cleanest oracles in
the suite.

The trap is that it is *so* easy that a vacuous test slips through. **Character
comparison blank-pads the shorter operand**, so comparing a buffer against a
shorter literal silently passes — a defect that has bitten this project
repeatedly. Every output helper therefore asserts `LEN` before equality, and the
widths vary so that padding is genuinely load-bearing rather than incidental.
Integer and BOZ editing were chosen first precisely because they involve no
reals and no processor-dependent kinds, so the arithmetic is exact.

### The substitution check, and a check on the check

For a **descriptor** packet the decisive non-vacuity test is **substituting the
descriptor** — the direct analogue of the operator-substitution sweep that caught
batch125 and batch127. Oracle and input mutation simply cannot detect a wrong
descriptor, because the oracle is wrong with it.

The reviewer re-ran all thirteen substitutions on both toolchains and all
failed. But the more interesting question is whether a substitution is
*load-bearing at all*: it only bites if the two descriptors actually **differ on
the chosen value**. I raised that explicitly, and it checks out —
`B4.4(5)` gives `'0101'` while `O` and `Z` give `'0005'`; `O4.4(8)` gives
`'0010'` while `B` gives `'1000'` and `Z` gives `'0008'`; `Z4.4(10)` gives
`'000A'` while `B` gives `'1010'` and `O` gives `'0012'`. Had any pair
coincided, that substitution would have appeared in the matrix while proving
nothing. The matrix is permanent in the generator.

### Source rules confirmed independently

`SS` suppresses the optional plus while a negative value's minus is
**mandatory**; output is right-justified and `w=0` uses the smallest positive
field width, but **`w=0` is prohibited on input**; `m` has **no effect** on
input; and lowercase hex `a`–`f` is equivalent on input.

That first rule drove a specific audit: **every positive-value output case uses
`SS`**, so none depends on the optional plus, which is processor dependent. The
single case without `SS` uses `-42`, where the minus is required — legitimate,
and confirmed rather than assumed.

Both toolchains pass 18/18, so no defect here. One observation was recorded
rather than blocked: `S13.7.2.4-007` also observes leading-zero padding while
leaving `BOZ-output-leading-zeros-to-m` pending — **under-claiming, not
vacuity**.
See `doc/source_audits/batch_140.json`.

## Batch 142 — list-directed input, and nine defects in one packet

The obvious next target in Clause 13 was list-directed I/O, and the first
decision was which half to test. **13.10.4 leaves list-directed *output* form
largely processor dependent** — field widths, separators and the representation
of many values are the processor's choice. Input is the opposite: 13.10.2 and
13.10.3 state exact obligations. So this packet tests **input only** and asserts
nothing whatsoever about output form.

That makes it the first packet to drive input through **`run.stdin_file`**.
`tests/fixtures/stop_io/` had already proved the harness supports it, but almost
nothing in the suite used it; the oracle stays entirely internal, since the
program reads a fixed record set and asserts the resulting *variable values*.

### Why the sentinel discipline mattered more here than anywhere

A **null value is defined by its absence of effect** — 13.10.3.2 p2 says it "has
no effect on the definition status of the corresponding list item". So the
oracle is *"the item still holds its prior value"*, and that is exactly the
shape of assertion this project has been burned by.

A **zero sentinel would be worthless**: uninitialized memory is commonly zero, so
a processor that never defined the item at all would pass. The audit confirms no
numeric sentinel is `0`; every null case **defines the item to a distinguished
value before the read**, so "unchanged" is a *positive* observation rather than
the absence of one; and the single `.false.` sentinel is not used for an
unchanged proof. Every character case asserts `LEN`, because comparison
blank-pads the shorter operand.

### Nine failures — one bug or nine?

The frozen LFortran target failed **nine of eighteen** cases while gfortran
passed 18/18. Nine failures in an eighteen-case packet is precisely the shape of
a **shared malformed test construct** rather than nine real defects, so that is
the question I put to the reviewer before allowing any XFAIL.

The answer was *neither*. They cluster into **three** areas of incomplete
list-directed handling — **repeat counts** (`r*c` and `r*`), **null values**, and
**slash termination** — and each required result is independently supported by
the pinned text, so each is filed on its own normative basis. They are also not a
harness artefact: the **other nine cases, built by the same generator through the
same stdin path, pass on the same toolchain**.

Each failure was reproduced by me before recording, and the expected-failure file
went from 819 to 828 lines.

Non-vacuity was proved by mutating the **feature**, not just the oracle: value
reorder, `3*7`→`2*7`, slash deletion and separator changes all fail as intended —
including on the subset that *passes* under frozen LFortran, which is exactly
where a vacuous test could have hidden.
See `doc/source_audits/batch_142.json`.

## Batch 141 — three rounds, and a finding against my own instruction

This packet proposed **18** facets across ten sections of 13.8 control edit
descriptors and shipped **16**. It is the second packet in the project's history
to need a **third review round**, after batch136 — and it failed in the same way,
which is the point worth recording.

### Round 1: two cases that failed on *both* toolchains

`LZS` and `LZP` were counted among the discharged facets, but both fail on
gfortran (compile-time "Missing comma in FORMAT string") *and* on frozen LFortran
(runtime "Missing comma between descriptors in format string").

The reviewer established from R1319, R1313, R1304 and R1303/C1302 that the
fixture format strings **are conforming and do contain the comma**, so this is an
implementation gap in *both* compilers rather than malformed test source. But
gfortran is this project's **f2023 reference**, so no reference validation
exists, and the batch130 precedent forbids a one-sided LFortran XFAIL in that
situation. Both facets went back to pending.

The `LZS`↔`LZP` **substitution** went with them: a substitution whose parent
fixture cannot run proves nothing, however good it looks in a mutation matrix.

### Round 2: the correction introduced a new defect — and it was mine

The corrected pending text said `LZS`/`LZP` affect **"F/E/EN/ES/EX"** output.
13.8.5 p3 says, verbatim:

> The LZS, LZP, and LZ edit descriptors affect only **F, E, D, and G** editing
> during the execution of an output statement.

`EN`, `ES` and `EX` are not in the list; `D` and `G` were missing from the
author's. I read 13.8.5 p3 from the pinned PDF myself before ruling.

**That wrong list came from my own correction instruction**, not from the
author's independent work. It is the second time this session a finding has been
upheld against my own guidance, and it is exactly why the standing rule exists:
**the pinned source outranks the coordinator's prompt**, and an instruction that
conflicts with the source must be *refused*, not followed. I restated that to the
author rather than quietly fixing it.

Two side questions came out of the same round. The author's own substitution
count was wrong — **8 reported, 9 actual**, with `TL2`→`TR2` omitted — so the
packet now states 9 substitutions and 7 descriptor omissions, each verified
load-bearing. And an unrequested "root import-path fix" was *investigated* rather
than reflexively rejected: it turns out `tests/test_contiguous_property_fixtures.py`
already does the same thing, it cannot mask a missing import, and discovery still
collects the module exactly once. Retained on precedent.

### What three rounds actually teaches

In both observed cases the new defect was in material the correction **newly
wrote**, not in what it removed. Removing a bad test is safe; the prose written to
replace it is not. That is the argument for re-verifying corrections rather than
trusting them, and it is why the withdrawn facets' *pending examples* were
themselves checked here: with `F3.1` on `0.5` the fractional digit means the zero
left of the decimal is the **optional** one per 13.7.2.3.2 p11, so `LZS`/`LZP`
genuinely determine it and the worked examples stand.
See `doc/source_audits/batch_141.json`.

## Batch 144 — the clean one, and why it was clean

Eighteen facets across 13.7.2.3.4 (EN) and 13.7.2.3.5 (ES), **accepted with zero
findings on the first round**. That is worth explaining, because it happened in
the same checkpoint where the other two fixture packets were blocked once and
*four* times.

Real-number output editing is the most **latitude-dense** corner of Clause 13.
The optional plus, the leading zero, the exponent digit count and the rounding
mode are all processor dependent, and every one of them is a way to write an
exact-string oracle that a conforming processor can legally fail. This packet
came back clean because all four were closed off **by construction, before any
code was written**: `SS` on every positive value, `E2` pinning the exponent
width, and only exactly-representable values whose discarded decimal digits are
all zero.

The reason those hazards were visible in advance is that **batch143 was being
blocked on exactly them at the same time**. Hazard knowledge transferred between
concurrent packets turns out to be worth considerably more than hazard knowledge
discovered in review.

### Six concerns posed in advance, all adjudicated against the text

**The leading-zero latitude does not extend to EN/ES.** This was the single
highest-risk question, since it is precisely what blocked batch143. 13.8.5 p3
says the LZ descriptors "affect only F, E, D, and G editing", and EN/ES
significands are fixed by the `yyy` and `y` forms rather than by an optional
leading zero. It genuinely does not apply.

**The exponent-digit-count facets could have been mis-attributed.** They might
have been about the *default* (no `Ee`) behaviour, in which case pinning `E2`
would discharge something the facet does not claim. They are not: "If `e` is
positive the exponent part contains `e` digits", plus Tables 13.2/13.3, put the
`E2` fixtures squarely on the rule they are filed under.

**The scale factor is settled by 13.8.6** — "On output, with EN, ES, and EX
editing, the scale factor has no effect." Here the *anti-vacuity* check matters
more than the rule: `1P`/`2P` **would** change `E` output, so the chosen scale
factors are load-bearing rather than no-ops, and `2P` was picked specifically to
make the `ES`→`E` substitution discriminate.

**EN/ES discrimination was verified by hand, not by compiler.** EN and ES
coincide for many values, so an `EN`↔`ES` substitution can sit in a mutation
matrix proving nothing. On the chosen values all three genuinely differ: `0.5`
gives EN `E-03`, ES `E-01`, E `E+00`; `100.0` gives EN `E+00`, ES `E+02`, E
`E+03`.

**Rounding was neutralised rather than pinned.** `0.5`, `0.125` and `100.0` are
exact in binary and every discarded decimal digit is zero — including in the
`d=2` cases — so the processor-dependent default rounding mode cannot change a
single asserted byte.
See `doc/source_audits/batch_144.json`.

## Batch 143 — four rounds, and a hole the discipline could not catch

Twenty-five facets of 13.7.2.3.2 F editing across **nineteen** fixtures, accepted
only after **four review rounds** and five blocking findings. It is the most
corrected packet in the project, and every round taught something.

### Round 1: an exact-string plan a conforming processor can fail

The packet asserted `WRITE(buf,'(SS,F4.1)') 0.5` gives exactly `" 0.5"`. But
p11 says leading zeros are not permitted "except for an **optional** zero
immediately to the left of the decimal symbol", mandatory only "if there would
otherwise be no digits in the output field". With `F4.1` on `0.5` the fractional
`5` *is* a digit, so the mandatory clause never applies, and 13.8.5 p2 leaves the
default mode `PROCESSOR_DEFINED`. A conforming processor may legally print
`"  .5"`.

Both compilers print the zero. That is exactly why **compiler consensus is not an
oracle**.

The replacement tests the mandatory half instead: `(SS,RZ,F3.0)` on `0.25` giving
`" 0."`, where `d=0` means omitting the zero would leave *no digits at all*. `RZ`
pins the otherwise processor-dependent rounding mode, and `UP` would give `"1."`
— which is what makes `RZ` load-bearing rather than decorative.

### Rounds 2 and 3: over-suppression, twice

Facets had been left pending claiming no portable oracle when exact ones existed
under the IEEE gate the packet already used — lowercase `inf` input, narrow
infinity output, and NaN output at `w=0` and narrow widths. (At `w=5` the payload
form is *impossible*, since `w-5 = 0`; that is precisely what forces `"  NaN"`.)

The fix was then only **partial**: `nan-empty-payload-quiet` stayed pending even
though p6 requires a **quiet** NaN for `NAN()`, and the fixture asserted only
`ieee_is_nan` — which establishes *a* NaN, not a quiet one. Standing lesson
recorded: **when fixing an over-suppression finding, re-audit the whole
catalogue, not the instances the reviewer named.**

The same round found a freshly added fixture reading into an **uninitialized**
variable. Demanding a whole-packet audit rather than a point fix immediately
revealed that **every** input fixture lacked a sentinel — including ones that had
already passed round 1.

### Round 4: the finding that justifies the whole method

Round 3 added the sentinels but never **mutated** them. A sentinel that is never
mutated is an unverified claim: if the oracle would pass anyway with the sentinel
removed, the fixture is still vacuous and the fix accomplished nothing. Thirty-six
permanent sentinel probes were added — remove the initializer, replace it with
the expected read result, replace it with `0.0`.

And the decisive probe exposed a hole **the ordinary discipline cannot catch**. A
quiet-NaN sentinel satisfies `ieee_class(value) == ieee_quiet_nan` with **no READ
occurring at all** — because the usual protection ("the sentinel must differ from
the expected value") relies on comparison, and **a NaN never compares equal to
itself**. The sentinel looks distinct while being indistinguishable to the
oracle. Closed with pre-READ guards; infinity needs none, since `+Inf` does
compare equal to itself. Recorded as followup `nan-sentinel-discipline-checklist`.

### Two other outcomes worth recording

I was **overruled, correctly**: I suspected `(SS,F0.1)` on `3.0` giving `"3.0"`
was non-portable, but 13.7.2.1(6) requires "the smallest positive actual field
width that does not result in a field filled with asterisks", which forces it.

And hexadecimal-significand input found LFortran genuinely wrong — it returns
`1.0, 1.5, 1.0, -1.0` where p7 requires `4.0, 3.0, 8.0, -4.0` — but gfortran
*also* rejects the form, so there is no reference validation, and the facets stay
pending with **no one-sided XFAIL**.

In all three multi-round packets so far (136, 141, 143) the late-round defect was
in material the correction **newly wrote**, not in what it removed. Removing a bad
test is safe; its replacement is not.
See `doc/source_audits/batch_143.json`.

## Batch 145 — opening Clause 12

Clause 12 was entirely untouched: **0 of 485 base units**. It is also the
declared I/O-statement dependency of Clause 13, which has been source-complete
since batch139 — so everything registered here propagates. This packet accounts
the first **36 base and 51 fine units** across 12.1 through 12.3.3.4, in eleven
catalogues with 65 requirement IDs and **zero unresolved units**.

### The priority was the mixed obligation/latitude sweep

That is the **dominant defect class** in this project, with five prior
occurrences: a single unit contains *both* an obligation *and* a grant of
processor latitude, and gets classified by whichever half is more memorable. The
rule is **symmetric** — latitude-plus-obligation must still yield a
`requirements` entry, and obligation-plus-latitude must still yield a
`permission` entry.

Clause 12 is unusually dense with "processor dependent" sitting in the same
paragraph as "shall", which makes a *missed* split the most likely defect here.
So the author was told outright that **an empty split list across 36 units of I/O
text would itself be suspicious**.

Ten splits came back: mixed obligation/latitude at 12.2.2#p1, 12.2.3#p1,
12.3.2#p3, 12.3.3.2#p2, 12.3.3.3#p2, 12.3.3.4#p3 and 12.3.3.4#p4; split
definition/latitude at 12.1#p4, 12.3.1#p3 and 12.3.3.1#p1. The reviewer verified
all ten are genuinely in the source *and* swept every other unit for a split
missed in the opposite direction, finding none.

### The boundary trap, avoided

A page range that stops exactly at a section boundary has produced mis-accounting
here before, so the reviewer read through physical page **246** and confirmed
12.3.3.4 ends before 12.3.4.1 begins. All 36 base and 51 fine unit hashes
verified against the census with no mismatches.

**Zero unresolved units** was treated as a strong claim and verified rather than
accepted — every unit is genuinely classifiable, none forced into a category to
avoid an `unresolved` entry.

### No over-suppression

Every "no portable oracle" claim — processor-dependent mappings, names, actions,
lengths and control characters, nonphysical records, the absent length of an
endfile record, preconnected `PRINT` and file identity, optional stream end
markers, unbounded stream length, cross-image identity — was audited for whether
a single-image program could observe *some* portable property even if not the
full behaviour. This mattered acutely: the sibling packet batch143 was blocked
**twice** for exactly that defect in the same checkpoint.

The source/fixture separation held as it must: `authored_facets` **unchanged**,
`tests/` untouched, and the unittest count identical to its own baseline. A
source packet binds no fixtures and earns no execution credit.
See `doc/source_audits/batch_145.json`.

## Batch 149 — rounding modes, and the first parallel wave

This is the first integration of **Checkpoint P**, which ran **eight packets at
once** — five Clause 12 source packets and three Clause 13 fixture packets —
instead of three. Authoring and review parallelise cleanly because packets on
disjoint sections touch disjoint catalogues; the bottleneck had been the serial
~20-minute full-suite gate, now replaced by a per-module parallel run that is
verified equivalent (all 1069 tests, all 70 modules) in about 6–7 minutes.

The packet itself covers 13.7.2.3.8 and 13.8.8: seventeen facets across six
fixtures, **accepted with zero findings**. This is the section that *defines*
rounding latitude, so the question was precisely what each mode requires. The
reviewer confirmed there is **no** latitude to substitute an unsupported mode —
UP, DOWN, ZERO, NEAREST and COMPATIBLE results are all required — and only
NEAREST ties and PROCESSOR_DEFINED are processor dependent. Neither is asserted.

Each mode pair is discriminated on an exactly representable value where the pair
genuinely differs: UP/DOWN on `1.25`, ZERO/DOWN on `-1.25`, RN/RU on the non-tie
`1.125`, and RC/RU on the exact tie `-1.25`. RN is never used on a tie, so the
tempting RN↔RC substitution — vacuous exactly where RN is processor dependent —
never appears.

One LFortran defect: `ROUND='DOWN'` on the **data-transfer statement** is ignored
(`1.25` prints `1.3`), while the same mode set through `OPEN` or through the `RD`
descriptor is honoured.
See `doc/source_audits/batch_149.json`.

## Batch 147 — E and D editing, and reaching exponent −100 portably

Nineteen facets of 13.7.2.3.3 across nineteen fixtures, after two rounds.

E and D differ from EN and ES in one decisive way: 13.8.5 p3 puts them in the
**LZ family**, so under scale factor 0 the zero before the decimal symbol is
*optional* — the same hazard that blocked batch143 four times. The packet handled
it by asserting only the forced slice of the field when `k <= 0`, and by using
`k > 0` layouts, which place a significant digit before the decimal symbol and
leave no optional position. Where Table 13.1 lets D choose its exponent spelling,
the oracle accepts exactly the permitted set `{D+00, E+00, +000}`.

The blocking finding was **over-suppression**. The table rows for
`99 < |exp| <= 999` had been left pending as needing a large real kind. The
reviewer showed they do not: the scale factor reduces the exponent by `k`, so
`(SS,101P,E110.101)` on the exact value `1.0` gives 101 digits, `.0`, and an
exponent of `-100` in the letterless `±z1z2z3` form — reachable on any
processor. Because `1.0` is exact, every extended digit is zero and neither
precision nor rounding has any latitude.

Frozen LFortran rejects that conforming format at runtime ("Got argument of type
(REAL), while the format specifier is (P)"), so both rows are recorded as
expected failures.
See `doc/source_audits/batch_147.json`.

## Batch 148 — L and A editing, and four ways a mutant can lie

Seventeen facets of 13.7.3 (L) and 13.7.4 (A) across fifteen fixtures, after
**four review rounds**. What makes this packet worth recording is that the
**oracles were correct from the first commit**. Every finding was about whether
the mutations actually proved anything — and each round found a different way
for a mutant to *look* load-bearing without being so.

1. **A mutant that fails by becoming non-conforming proves nothing.** `L4`→`I4`
   on a logical item fails because I editing requires an integer (13.7.2.2 p1),
   not because I and L interpret the field differently.
2. **Removing a bad mutant can leave no feature mutation at all.** Two fixtures
   were left with only input mutations, hidden by an allowlist in the test
   module.
3. **Changing the datum to make room for a mutant can change the facet.** Moving
   `'   F'` to `'  FT'` quietly made the "standard false form" facet depend on
   the trailing-characters sentence as well.
4. **A mutant that reads a different planted value tests the datum, not the
   feature.** `L4`→`T4,L1` would be "detected" even on a processor that ignored
   the L width entirely.

The final mutants are plain width substitutions — `L4`→`L3` on `'   F'`,
`L2`→`L1` on `'.f'` — that push the decisive `F` out of the field. The subtle
part is that the narrowed fields `'   '` and `'.'` are *not* standard forms, so a
conforming processor may reject them *or* accept them as an extension. A mutant
whose outcome is processor dependent is only load-bearing on some processors. So
each fixture now reads a separate one-character boundary field under `IOSTAT` and
asserts all three of `ios == 0`, the first value `.false.`, and the boundary
`.true.`: rejection makes `ios` nonzero, and acceptance shifts the next `L1` onto
the planted `F`. **No conforming behaviour satisfies all three.**
See `doc/source_audits/batch_148.json`.

## Batch 153 — the io-control-spec constraints

This packet registers 12.6.2.1, the thirty units that govern every specifier in a
data transfer statement's control list. Twenty-four are **numbered** rules
(R1213, R1214, C1210–C1231), and numbered constraints are required to be
diagnosed — so this is one of the richest sources of genuine negative facets in
Clause 12. It took two rounds.

The first round was blocked because the packet claimed **zero** mixed
permission/restriction units, which across thirty units of constraint text is
itself a warning sign. C1223 says an `ADVANCE=` specifier "shall appear *only*
in" certain statements, which admits `ADVANCE=` there as well as forbidding it
elsewhere; C1230's "either … or" does the same for `DELIM=`. Both are now split.
For C1211, C1218, C1219 and C1226 the admission turns out to be owned by the
syntax rule R1213, and that decision is now recorded rather than assumed.

C1215 had lost half of a compound obligation: the `ERR=`/`EOR=`/`END=` label must
be a branch target **and** appear in the same inclusive scope. The reviewer
derived from the definitions that an inclusive scope *includes* nested `BLOCK`s,
so only a label in an internal procedure is a valid negative for the second half.
And a C1224 negative (`EOR=` without `ADVANCE=`) unavoidably also violates the
unnumbered p2; C1224 is recorded as the only diagnosable rule in that overlap.
See `doc/source_audits/batch_153.json`.

## Batch 158 — pointer assignment syntax, and five missing diagnostics

Twenty facets of 10.2.2.2 across twenty-three fixtures, after two rounds. The
admission cases observe **non-default** bounds — `p(-4:,6:)` and
`p(-1:0,4:6)` — because a default lower bound of 1 would satisfy an LBOUND
oracle vacuously, and they check aliasing in both directions from distinguished
non-zero values.

The one blocking finding was a mutant that proved nothing: removing the remap
list turned a rank-2 pointer assignment to a rank-1 target into a C1022
violation, so its "failure" was a compile error rather than evidence about
remapping. It was replaced by a conforming lower-bound shift.

Frozen LFortran fails five of the negatives, each confirmed independently: it
**accepts** a type mismatch, a kind-parameter mismatch, a rank mismatch and a
non-TARGET target — all constraints it is required to diagnose — and it crashes
on a vector-subscripted target, which is not a diagnosis.
See `doc/source_audits/batch_158.json`.

## Batch 157 — the form of the DO construct

Twenty facets of 11.1.7.2 across twenty fixtures, after two rounds. This section
is about **form**, so the packet deliberately claims nothing from the execution
semantics of 11.1.7.4 and 11.1.7.5. Each admission fixture instead proves that a
form is parsed *as that form* with an iteration trace that a plausible mis-parse
would get wrong — label-DO fixtures, for example, carry a counter after the
labeled statement that must **not** advance per iteration.

The single finding was a quiet one: the two C1135 negatives had been generated by
copying their controls and changing only the `END DO` line, so their source
headers still named the control's rule and facet. The unit test merely counted
headers. It now compares every header against the manifest.
See `doc/source_audits/batch_157.json`.

## Batch 154 — DATA statements, and the cases that were withheld

Twenty-four facets of 8.6.7 across thirteen fixtures, after two rounds, drawn
from the largest backlog in the suite (182 pending facets).

The most important finding was about **what was not shipped**. The author had
probed DATA on a triplet section, a vector-subscript section, a component
section and a negative-step implied-DO, found that frozen LFortran failed all four
while gfortran passed, and quietly left the facets pending. That is exactly
backwards: when the text backs the reference, an LFortran-only failure is a
**defect to record**, not a reason to leave a facet untested. All four now ship
with order-discriminating values, and all four are recorded as LFortran failures
— a crash, two wrong-order results and an LLVM verification error.

The other two findings were about mutation quality. Twelve repeat-factor mutants
broke the value-count equality of 8.6.7 p8 and so failed at compile time, proving
nothing about repeats; they were replaced by balanced substitutions. And every
fixture now has a conforming "replace the DATA" probe — the pointer probe
retargets to another initialized target rather than leaving the association
undefined.

Integration also had to renew three pre-existing DATA position reviews, at their
own original state, because binding new facets into the shared catalogue
re-fingerprinted them.
See `doc/source_audits/batch_154.json`.

## Batch 159 — array constructor forms, on a shared catalogue

Twenty facets of 7.8 across fifteen fixtures, after two rounds. The complication
was ownership: batch130's value generator already binds facets in the same
catalogue and renders the same view, and this packet's first attempt broke that
generator's `--check`. The fix composes the view deterministically through the
older renderer, changed only enough to recognise the new packet's validated
bindings; its own fixtures, partition and unknown-facet validation are untouched,
and both generators now check clean in either order.

The second finding was that six runtime fixtures shipped with **no mutations at
all**. Every one now carries a conforming feature mutation — swapped implied-DO
nesting, reversed or dropped values with the size adjusted, a changed type-spec
length — run by a permanent mutation check.
See `doc/source_audits/batch_159.json`.

## Batch 146 — file position and internal files

Thirty-one units across 12.3.4 through 12.4, accepted with no findings. The most
useful part is 12.4, internal files: the mechanism every Clause 13 fixture already
relies on to observe formatted output byte-exactly is now registered with its own
obligations — a record is the variable, the remainder of a record written is blank
filled — so those tests' foundations are themselves accounted for. The splits at
12.3.4.2, 12.3.4.3, 12.3.4.4, 12.3.5 and across the fifteen fine units of 12.4
were verified, and the octet storage-unit statement is correctly a
recommendation. This was also the first packet of the parallel wave whose
`index.json` insert conflicted with a sibling on cherry-pick; resolving it by
section order is routine.
See `doc/source_audits/batch_146.json`.

The historical PARAMETER and IMPLICIT author contexts are
batch076's2,056cases/129catalogues. DATA, IMPORT and NAMELIST were authored
from batch078's2,056cases/133catalogues; their separate candidate counts must
not be conflated with current main or with each other.
The original PARAMETER native capture completed before a Python3.9 proof-join
error; its unchanged report was joined using the existing Python3.12
environment, with no rerun and no invented runner-return value.

The EQUIVALENCE8.10.1.1-.5 source proposal `8cf739ab` is frozen from
`ddb0952`:25base/129fine units,21requirements and130pending facets. It is
now independently reviewed and registered as batch085 in the current
147-catalogue main context; the author's original frozen context and its
uncommitted index overlay are not relabelled as that integration. The
separately authored
COMMON packet retains its original `cb45d6a`/2,062-case context, despite its
source-only registration in batch084's newer main context.
The main baseline remains `b153c75b`, including the two approved PARAMETER
failures. All wider source/oracle/processor gates remain unfinished.

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
