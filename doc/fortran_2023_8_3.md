# Fortran 2023 8.3: Local type-parameter entry capture

**Source review: reviewed.** Current fixture/evidence adjudications are separate content-bound records. This generated subset has five shared valid/effect/run/f2023 programs representing seven S8.3-001 facets. 4 C814 facets and 2 other S8.3-001 facets remain PENDING. This packet changes no8.4source, fixture or facet.

Authority: J3/24-007,18December2023,688physical PDF pages,
SHA-256 `7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
Original8.3 is on PDF119 between the8.3 and8.4headings. Its3base/19fine/22accounting units, 2requirements and18facet IDs are preserved. The original source review in `doc/source_audits/batch_027.json` does not automatically adjudicate these new inputs.

## Exact premises and boundaries

The local CHARACTER subjects meet3.151.2: they are not dummy arguments, global entities or exported objects. Their declaring subprogram/BLOCK determines entry. Contained-scope access to the outer object follows5.4.3.2.2p2; it does not recapture the outer parameter at inner entry. BLOCK declarations are construct entities under11.1.4/19.4, not host statement entities.

Under10.1.11p1/p2(2)/(4)/p6, previously declared nonoptional INTEGER INTENT(INOUT) n and the defined host integer supply restricted, nonconstant value expressions. Executable assignments of2/3/4/5 do not make n PARAMETER or a constant expression. The individual length uses R723's *(n) parentheses. All actuals are defined before calls, and INOUT sources remain definable for the OUT helper under15.5.2.5p20. Internal procedures provide complete explicit interfaces.

No local character declaration has an initializer, SAVE, POINTER or ALLOCATABLE. Its payload is assigned only in the body after parameter establishment. LEN16.9.122 inspects the actual named local data object and is compared with an independent scalar literal. Payload guards follow definition and a separate LEN guard, so padded comparison alone cannot conceal a wrong length. No RANK, KIND-code, byte/encoding, floating, descriptor, allocation-status or pointer query is used.

The source mutation occurs after entry, without assuming left-to-right specification-expression ordering. 11.1.4p3 establishes BLOCK specifications before its body. The OUT helper does not assign or read its dummy:19.6.6p1(15)(b)/(c) and8.5.10p3 supply the undefinition event. Only the source integer is left undefined; local payloads stay defined. LEN/payload checks do not reference that integer, which is then restored by literal assignment before any later use. No poisoning, changed-bit expectation or trap is an oracle.

Fresh2/4procedure calls use the same procedure, and3/5BLOCK entries use the same syntactic BLOCK in a two-iteration ordinary DO. Explicit entry ordinals, totals and57primitive checks plus5completion guards detect missing/extra entries. Counters are ordinary live main-program integers initialized by executable assignment; their use is not SAVE-retention or specification-function-order coverage. Nested3/5objects are checked against separate literals while both are alive, after source n becomes7.

Unsupported compilation or runtime behavior remains a failed run contract, never an admission, skip or weakened fixed-length declaration. Full-program single-span wrong-oracle probes use only processors that genuinely execute the current parent; they are empirical observer tests outside inventory, not intrinsic correctness proof or approval. Actual f2018 observations are not promoted to f2023.

## Definitions

<!-- BEGIN GENERATED 8.3 -->

### C814: Automatic data objects cannot have SAVE

**Source:** 8.3 C814 and p1 antecedent, physical PDF119, printed105, lines2-4 **Class:** Restriction.

**Definition:** SAVE is excluded for an automatic data object as defined by p1: a nondummy data object
with a type parameter or array bound depending on a nonconstant specification
expression. The formal expression and entity predicates matter, not observed size,
storage placement, or simply the appearance of a variable name in an inquiry. An
inferred SAVE has not become harmless merely because no SAVE keyword appears, but
initialization and other inferred routes retain their own restrictions.

**Diagnostic obligation:** required.

**Facets:** `character-selector-save`, `character-entity-length-save`, `explicit-bound-save`, `pdt-length-save`, `fixed-length-allocatable-save`, `fixed-length-pointer-save`, `inquiry-dependent-bound-save`, `constant-specification-admission`, `bare-save-admission`.

**Oracle:** Seven focused automatic/SAVE report-control families and two bounded compile-admission
families. Each negative is otherwise conforming and its repair changes only the selected
SAVE specification. Numbered reporting capability permits an ordinary0 or nonzero return
with a real located causal report; neither fatal rejection nor particular English
wording is mandated.

Bounded automatic-SAVE implementation: ten compile/f2023 fixtures represent five
selected facets. Three complete procedures put SAVE on a nondummy automatic CHARACTER
selector-length local, a CHARACTER individual *(n) local, and an ordinary INTEGER a(n),
with previously typed nonoptional INTEGER INTENT(IN) n. Their exact controls delete only
', save', retaining the same automatic local, dummy and executable body. Three distinct
constant-specification controls use a prior INTEGER PARAMETER, LEN of a previously
fixed-length CHARACTER object, or SIZE of a previously fixed-shape ordinary INTEGER
array; neither inquiry reads payload. The seventh positive control has one no-list SAVE
in a procedure: allowed-item filtering excludes the automatic local, without a retention
claim. Reporting uses actual located automatic-object/SAVE causes, permits ordinary
zero/nonzero and qualified nonfatal reporting, and requires no printed rule code or
fatal-return policy.

**Oracle limitation:** Four C814 facets remain pending: PDT length, fixed-length ALLOCATABLE, fixed-length
POINTER, and inquiry-dependent-bound negatives. The three selected controls remain
automatic locals, not dummies, results or constants. No declaration initialization,
pointer/allocatable/deferred/assumed shape, BLOCK no-list SAVE, retention run,
bound/parameter-capture effect or definition-use credit is added. Fixed LEN/SIZE inquiry
arguments have known declared properties; their uninitialized payload is never read.
Bare SAVE/nonconstant words, echoes, wrong entities/attributes, malformed suffixes,
unrelated initializer/eligibility/interface errors, unsupported/unimplemented
facilities, Internal/verifier/resource failures and recovery do not corroborate C814.
Generation preserves independent source/case/inventory adjudications; representation and
processor agreement are not approval, and actual unsupported/reference failures remain
recorded observations.

**Dependencies:** 3.151.2; 4.1.2/4.2; 7.2 C701/C702; 7.4.4.2 R723; 7.5.3; 8.2 C805/C808; 8.5.8.2/.4,
8.5.13 C853, 8.5.16 C861/C862; 8.6.7 C880; 8.6.14 R859/C893; 8.7; 10.1.11 R1029/C1011
and10.1.12 C1012; 11.1.4 C1108 and NOTE; 16.1/16.9.122/16.9.194.

### S8.3-001: Nonconstant local type parameters are established at entry

**Source:** 8.3 p2, physical PDF119, printed105, lines5-9 **Class:** Effect.

**Definition:** For a local variable of a subprogram or BLOCK, a type parameter defined by a nonconstant
expression in the declaration-type-spec or individual char-length is established upon
entry to a procedure defined by that subprogram, or execution of the BLOCK statement.
Redefining or undefining variables used by the expression does not change that
established parameter during the corresponding execution. This is not the separate
array-bound capture rule and does not turn deferred or assumed markers into ordinary
nonconstant expressions.

**Diagnostic obligation:** not-required.

**Facets:** `procedure-selector-snapshot`, `procedure-entity-length-snapshot`, `block-selector-snapshot`, `block-entity-length-snapshot`, `pdt-length-snapshot`, `fixed-length-descriptor-snapshot`, `post-undefinition-snapshot`, `fresh-entry-captures`, `nested-block-snapshots`.

**Oracle:** All planned executions observe defined local type parameters against independent small
integers; text/component values are defined before value reads. Repeated and nested
entries prevent a one-time global capture from standing in for the per-entry rule.
Undefinition is a source state transition, not permission to observe an undefined source
value.

Finite entry-capture implementation: five complete valid/effect/run/f2023 programs
represent only the seven authorized procedure/BLOCK/undefinition/fresh/nested facets.
Named local ordinary CHARACTER objects have nonconstant n-dependent selector or
parenthesized individual lengths and no declaration initialization. Executable
assignments define payloads after entry; independent literal LEN, payload, source-state
and positive entry/count guards are consumed. The INTENT(OUT) helper leaves only the
source integer undefined; no source value is read until literal restoration.
Specification-expression ordering, SAVE retention,
PDT/descriptor/RANK/intrinsic/source-use and other-owner coverage are not added.
Original source-review administrative fields remain unchanged, so their binding may
become stale without renewal.

**Oracle limitation:** No negative twin for this effect and no downgrade to compile-only when a feature is
unsupported. Array-bound invariance, deferred-parameter changes and alternate
procedure/result roles remain their canonical dependencies, not silently added p2
obligations. Source-use infrastructure remains pending. RANK requires a DATA OBJECT: no
direct RANK constructor/expression probe, and no fixed-rank destination used to prove a
constructor's rank. If such a separate witness is needed later, use a correctly
associated assumed-rank dummy data object with the original C839/C840 and argument
rules.

**Dependencies:** 3.151.2; 5.4.3.2.1/.3 and5.4.5; 6.2.3 R604/R605; 7.2 C701/C702 and deferred/assumed
routes; 7.4.4.2; 7.5.3.1; 8.2 C805/C808; 8.5.8.2/.4/.7; 9.2 R902/C901/C902; 10.1.11/.12;
11.1.4 p3; 15.5.2.4; 16.1,16.9.122 and16.9.171p3; 19.6.6p1(15).

<!-- END GENERATED 8.3 -->

## Finite entry and oracle bindings

### `S8_3_001_valid__type_parameter_entry_procedures`

**Facets:** `procedure-selector-snapshot`, `procedure-entity-length-snapshot`.

* `procedure_selector`: procedure; `character(len=n) :: text`; source entry `2`, later `5`; literal LEN `2` and body-defined `ab`.
* `procedure_entity`: procedure; `character :: text*(n)`; source entry `3`, later `7`; literal LEN `3` and body-defined `abc`.

Expected completed primitive guards: `9`. Guard spans bind the actual scalar expectations.

### `S8_3_001_valid__type_parameter_entry_blocks`

**Facets:** `block-selector-snapshot`, `block-entity-length-snapshot`.

* `block_selector`: block; `character(len=n) :: text`; source entry `3`, later `7`; literal LEN `3` and body-defined `abc`.
* `block_entity`: block; `character :: text*(n)`; source entry `2`, later `5`; literal LEN `2` and body-defined `ab`.

Expected completed primitive guards: `9`. Guard spans bind the actual scalar expectations.

### `S8_3_001_valid__type_parameter_entry_post_undefinition`

**Facets:** `post-undefinition-snapshot`.

* `undefined_procedure`: procedure; `character(len=n) :: text`; source entry `3`, later `undefined`; literal LEN `3` and body-defined `abc`; source restored to literal `5` before reuse.
* `undefined_block`: block; `character(len=n) :: text`; source entry `3`, later `undefined`; literal LEN `3` and body-defined `abc`; source restored to literal `7` before reuse.

Expected completed primitive guards: `10`. Guard spans bind the actual scalar expectations.

### `S8_3_001_valid__type_parameter_entry_fresh_entries`

**Facets:** `fresh-entry-captures`.

* `fresh_procedure_first`: same-procedure; `character(len=n) :: text`; source entry `2`, later `7`; literal LEN `2` and body-defined `ab`.
* `fresh_procedure_second`: same-procedure; `character(len=n) :: text`; source entry `4`, later `7`; literal LEN `4` and body-defined `abcd`.
* `fresh_block_first`: same-block; `character(len=n) :: text`; source entry `3`, later `7`; literal LEN `3` and body-defined `abc`.
* `fresh_block_second`: same-block; `character(len=n) :: text`; source entry `5`, later `7`; literal LEN `5` and body-defined `abcde`.

Expected completed primitive guards: `18`. Guard spans bind the actual scalar expectations.

### `S8_3_001_valid__type_parameter_entry_nested_blocks`

**Facets:** `nested-block-snapshots`.

* `nested_outer`: outer-block; `character(len=n) :: outer_text`; source entry `3`, later `5`; literal LEN `3` and body-defined `abc`.
* `nested_inner`: inner-block; `character(len=n) :: inner_text`; source entry `5`, later `7`; literal LEN `5` and body-defined `abcde`.

Expected completed primitive guards: `11`. Guard spans bind the actual scalar expectations.

## Complete unselected pending plans

### C814

* **`pdt-length-save`** - PENDING a complete visible PDT with one LEN parameter and an ordinary INTEGER array component bounded by it; a local TYPE(t(n)) object has SAVE and no initializer. Remove only SAVE. Its KIND parameters, if any, are constant and never guessed intrinsic kind codes. Unsupported PDT machinery or a wrong component specification is not C814 evidence.
* **`fixed-length-allocatable-save`** - PENDING scalar CHARACTER(LEN=n), ALLOCATABLE, SAVE with eligible nonconstant n and no initialization. Remove only SAVE. The nondeferred length, not the later allocation, gives the automatic-object premise. Do not introduce an illegal explicit-shape allocatable array or read unallocated data.
* **`fixed-length-pointer-save`** - PENDING scalar CHARACTER(LEN=n), POINTER, SAVE with no initialization. Remove only SAVE; its nondeferred length is the selected premise. No pointer target, association inquiry or C770 lifetime defect is introduced. A POINTER attribute is not a universal exemption from automatic classification.
* **`inquiry-dependent-bound-save`** - PENDING local INTEGER a(SIZE(arg)) with SAVE, where arg is an assumed-shape INTEGER dummy in a complete explicit-interface procedure. Its extent is not a constant expression. Remove only SAVE; distinguish the actual automatic/SAVE cause from missing-interface, wrong-rank or unsupported inquiry reports.

### S8.3-001

* **`pdt-length-snapshot`** - PENDING runtime local object of one complete PDT with a LEN parameter n=2 and an ordinary INTEGER array component. After entry define every component element, change the source dummy to5, and independently require parameter2, component extent2 and the assigned literal values. LEN is not a runtime KIND selector, and an arbitrary PDT LEN is not universally a CHARACTER length.
* **`fixed-length-descriptor-snapshot`** - PENDING two finite runtime contexts with local nondeferred CHARACTER(LEN=n) ALLOCATABLE and POINTER scalars, initially n=2. Change n to5 after entry; allocate the allocatable without a new type-spec or associate the pointer with a live, defined, matching-length target. Check established length2 and defined text. Keep allocation/association separate from entry capture; do not replace the fixed length with colon or inspect unavailable deferred parameters.

## Validation and remaining gates

`python3 -B tools/generate_type_parameter_entry_fixtures.py --check` verifies exact files and owned rendering. Targeted source/definedness/interface/entry-sequence/literal and metadata tests accompany the generator. The original author packet preserved its1972-case base, nine links and empty SourceUses. This generator does not renew source, fixture, link or inventory reviews; subsequent coordinator adjudications are read from their current records. Authorship and representation do not confer source/fixture/oracle/evidence approval.
