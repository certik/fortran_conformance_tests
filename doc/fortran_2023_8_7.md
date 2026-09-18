# Fortran 2023 8.7: IMPLICIT statement

The canonical catalogue is `doc/catalogues/implicit_statement_8_7.json`.
Effective source review comes from
`Registry.catalogue_review_state("8.7")`; current facet states remain in
the catalogue. Source classification alone grants no fixture, source-use,
canonical-link, inventory or processor-conformance approval.

This scope is the complete original 8.7 of J3/24-007, December18,2023,
688 pages, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
It begins on physical PDF141, printed127, and ends at the actual 8.8
heading on physical PDF143, printed129. The complete section hash is
`9ab08225c68e869d2d27b896f397667280d9d8c8078e9aa1df78f58590b7dfaf`.
All18base units are included: p1, R866-R869, C895-C899, p2-p4 and
notes1,2,2.2,3,4. Note2's program and explanation continue onto PDF143.
In the pinned draft, 8.8 is IMPORT and 8.9 is NAMELIST; neither is an
authored catalogue in this packet.

## Grammar and independent duties

Ordinary IMPLICIT requires an implicit-spec list. NONE has independently
optional parentheses and an optional inner specifier list. Consequently
bare NONE and NONE() are both admitted spellings of the absent-list
branch. NONE(TYPE) selects a null type map; NONE(EXTERNAL) alone does
not. A distinct TYPE/EXTERNAL pair in either order selects both duties,
but two separate NONE statements are not equivalent.

R867 uses the actual declaration-type-spec production R703. It does not
make every R703 alternative legal in every context: TYPEOF/CLASSOF have
C709's statement-location restriction, CLASS and assumed-type entities
have their category restrictions, and kind/length/type parameters retain
their real specification and interface conditions. Selector parentheses
inside a type are not the final letter-list parentheses.

Kinds are not portable integer codes. Initial source plans can use
KIND(0), KIND(0.0), KIND(0.0D0) and other appropriate supported
inquiries; selected nondefault kinds need actual support/profile
qualification. CHARACTER length, assumed/deferred parameters and
parameterized derived types have their distinct owners. No direct real
BOZ assignment, IEEE/model/profile decision or existing conversion
distinction is changed by an implicit map.

The syntactic class letter is defined in 6.1.2, not by inventing a
letter-name production. R603 defines names elsewhere; the complete
502-rule head scan and the original productions remain the source
authority. A range includes its endpoints and intervening alphabetic
letters. C898 requires the second endpoint to follow the first strictly:
equal and descending endpoints are not admitted ranges. Case equivalence
does not create separate letter namespaces, and no character-code
arithmetic or collating-sequence assumption is used.

## Cardinality, ordering and mappings

C895 requires every NONE form to precede PARAMETER statements and limits
NONE to one per scoping unit. C896 prohibits repeated TYPE or EXTERNAL
inside one statement. C897 excludes other IMPLICIT statements when NONE
has TYPE or no list; EXTERNAL-only has a different antecedent. General
statement ordering still applies. The original Table5.1 was read as a
diagram, including its horizontal and vertical boundaries; initial
coexistence controls place NONE(EXTERNAL) before ordinary mapping
statements rather than treating a false C897 antecedent as a general
ordering exemption.

The p2 range/list equivalence is a definition. Its separate no-repeated-
letter obligation becomes S8.7-001, a prose restriction without an
automatic mandatory-diagnosis policy. S8.7-002 similarly records p4's
prior-IMPLICIT-or-default mapping obligation. No prior local S8.7 IDs
exist in the exact parent. Existing C710 prior-type establishment,
S8.6.7-002 DATA confirmation and S8.6.11-001 PARAMETER subsequent-
declaration rules keep their own source, cases and pending plans.
The new S IDs do not become empty runtime map classifiers.

The remaining p1/p3/p4 mechanisms are source definitions or permissions.
Each scope has mappings for all26letters, possibly null. A specified
entry overrides the applicable default for that letter. The text names
program units and interface bodies for default INTEGER on I-N and
default REAL otherwise; BLOCK, internal subprogram and module subprogram
defaults follow the host map. Unit, submodule, module-subprogram and
module-procedure-interface classifications must follow their actual
grammar and scope rules, not a word match or compiler convention.

An interface body's own default is not automatically the containing
module's null map. IMPORT selects host entities, not a wholesale implicit
map transfer. An otherwise implicit name appearing only in BLOCK is not
thereby a separately declared construct variable: note3's NSQP belongs
to the inclusive subroutine scope. Explicit construct declarations,
IMPORT accessibility and host shadowing are separate mechanisms.

Explicitly type-declared data, intrinsic functions, components and
USE/HOST-associated entities are outside p4's implicit-declaration
antecedent. An inner IMPLICIT INTEGER(C) does not retype an existing
host-associated COMPLEX C. A type-name hidden by a local integer can
still be the type identity denoted by an inherited mapping. An explicit
FUNCTION type prefix overrides the result's implicit map, but the actual
result name and prohibition on specifying its type both ways remain
15.6.2.2 requirements.

## EXTERNAL and complete evidence contexts

C899 requires an external or dummy procedure name in the specified
scope, a contained subprogram or a BLOCK to have an explicit interface
**or** an explicit EXTERNAL declaration. A real result-type declaration
alone is not that declaration. NONE(TYPE) alone does not select the
EXTERNAL duty, and a child typing statement does not cancel a parent's
stated C899 duty.

Procedure roles must be established. Under 15.2.2.3 a dummy appearing as
a procedure designator in a reference is a dummy procedure; an ordinary
scalar data dummy is not interchangeable with it. Internal/module/
intrinsic procedures have their actual interface rules. A PROCEDURE
declaration specifies EXTERNAL, and an interface body is another
establishing route; self/interface EXTERNAL declarations can themselves
be prohibited by C843/C844. A function's result identifier is not
unconditionally its external-procedure identifier. Actual-procedure
arguments and pointer targets retain the separate 8.5.9p2 duty.

Future negatives need complete matching providers, interfaces, callers,
declarations and source-minimal repairs. A missing library, wrong
argument type, undefined payload or unrelated expected-token report
cannot stand for an IMPLICIT condition. The numbered reporting duty is
not a requirement for fatal status, printed rule numbers or one
diagnostic vocabulary. Prose restrictions do not acquire that numbered
diagnostic duty merely because they use shall.

All notes are informative examples, not ready-made passing programs.
The ellipses, missing providers and actual argument values in notes1/4
must be completed. Note2/2.2's host B needs defined components before
an executed assignment to AA. Note3's definition/use guards must be
preserved rather than reading an undefined variable. These are not
opportunities to fabricate no-op runs or numerical oracles.

The exact parent has existing lexical IMPLICIT NONE and C709/C710
owners, but no primary R866-R869/C895-C899 cases or direct 8.7
case/link source anchors. Any future reuse needs separately adjudicated
complete programs, actual occurrences, roles and fingerprints. This
source packet adds no fixture, compiler observation, link, SourceUse,
baseline entry or inventory renewal. Global source coverage remains
incomplete.

<!-- BEGIN GENERATED 8.7 -->

### R866: IMPLICIT has a typed-list form and a NONE form with independently optional parentheses and specifiers

**Source:** 8.7 R866, J3/24-007,18December2023, physical PDF141, printed127. **Class:** Syntax.

**Definition:** The ordinary form has a nonempty implicit-spec list. The alternative is IMPLICIT NONE
with optional parentheses that themselves may contain an implicit-none-spec list or be
empty. NONE, NONE(), NONE(TYPE), NONE(EXTERNAL) and a distinct TYPE/EXTERNAL pair have
separate grammatical and semantic premises. The ordinary type map and EXTERNAL duty are
not interchangeable; the governing C895-C899 and p3-p4 interpretations remain explicit.

**Diagnostic obligation:** required.

**Facets:** `ordinary-typed-list`, `plain-NONE`, `empty-parentheses-NONE`, `TYPE-only-NONE`, `EXTERNAL-only-NONE`, `combined-NONE-specifiers`, `NONE-parentheses-and-list-syntax`, `default-null-and-host-map-source`, `canonical-source-occurrence-boundary`.

**Oracle:** Complete statement admissions and source-minimal grammatical contrasts, with exact
mapping/EXTERNAL branch, scope, ordering and canonical type/interface prerequisites. The
source interpretation determines the oracle; neither one compiler's vocabulary nor an
empty run proves mapping semantics.

**Oracle limitation:** Required reporting capability is not obligatory fatal status, printed R866 or fixed
English. Future complete diagnostics need their real forbidden form, control, phase/mode
and legitimate staged origin. Unsupported facilities, arbitrary error tokens, echoes,
wrong scopes, missing providers or native/internal/resource failures do not establish
the intended predicate. No current observation, coverage, approval or whole-standard
completion is supplied.

**Dependencies:** 4.1.1-.3/R401;4.2;5.1R504-R506;5.3.2Tables5.1-5.2;R867-R869/C895-C899/p3-p4;7.3.2.1;8.5.9;14.2.3;15.4.2.1/.2;15.6.2.5;19.4;19.5.1.4.

### R867: An implicit specification combines a qualified declaration type with a nonempty letter list

**Source:** 8.7 R867, physical PDF141. **Class:** Syntax.

**Definition:** An implicit-spec is a declaration-type-spec followed by a parenthesized nonempty
letter-spec list. R703 supplies the actual type alternatives; its global restrictions
are not waived by this context. Kind/length selectors within the type are distinct from
the final letter-list parentheses, and neither numeric kind values nor blanket
acceptance of every R703 alternative is implied.

**Diagnostic obligation:** required.

**Facets:** `intrinsic-type-maps`, `kind-selector-source`, `character-length-and-kind`, `derived-type-identity-map`, `parameterized-polymorphic-assumed-source`, `TYPEOF-CLASSOF-exclusion-source`, `letter-list-parentheses`, `entity-exemptions-and-prefix-source`.

**Oracle:** Resolve the canonical type specification and complete entity/scope context before
mapping the letters. Every kind, length, derived-type identity and interface premise is
explicit; source relationships and finite admissions remain pending rather than becoming
empty execution classifiers.

**Oracle limitation:** Type mapping does not define values, choose literal suffixes, allocate objects or
establish pointer association. Nonconstant/unsupported selectors, inaccessible
definitions, invalid polymorphic/assumed categories and missing interfaces cannot be
disguised as R867 syntax. Compiler agreement cannot replace the original type rules, and
no preexisting real-BOZ/profile decision is renewed.

**Dependencies:** R703/C704-C714;7.3.2.1-.3;7.4.1R704-R706/C717;7.4.3.1/.2;7.4.4.1/.2C724-C731;7.4.5;7.5.3.2;7.5.9;R868/p3-p4/notes1-2.2;8.2;8.6.11;10.1.11/.12;14.2.2;15.4.2;15.6.2.2;19.5.1.4.

### R868: A letter specification is one letter or a minus-separated two-letter range

**Source:** 8.7 R868, physical PDF141. **Class:** Syntax.

**Definition:** A letter-spec begins with a letter and optionally appends a minus and a second letter.
The syntax class is the26letters defined in6.1.2, not an arbitrary name or a
variable/expression. C898 requires strictly ascending endpoints; p2 defines inclusive
expansion and independently forbids repeated membership.

**Diagnostic obligation:** required.

**Facets:** `single-letter-form`, `two-letter-range-form`, `missing-endpoint-repair`, `letter-not-name-or-value`, `case-and-list-wrapper-source`.

**Oracle:** Complete lexical/range forms with source-minimal single-defect repairs and separately
established type-list context. The explicit syntactic class letter and canonical
name/list rules determine roles.

**Oracle limitation:** R868 does not permit digits, underscores, arbitrary names, missing endpoints or
character-value expressions merely because a compiler accepts them. It does not impose
the prose nonoverlap condition as a new numbered syntax rule. Reporting is capability
without mandatory status, wording or code.

**Dependencies:** 6.1.1R601;6.1.2p1-p3;6.2.2R603;R867/C898/p2;4.1.3R401;4.2p2.

### R869: The NONE specifier alternatives are EXTERNAL and TYPE

**Source:** 8.7 R869, physical PDF141. **Class:** Syntax.

**Definition:** Each implicit-none-spec is EXTERNAL or TYPE. The alternatives select different duties,
may appear together once each in one list, and are not type names or arbitrary feature
keywords. R866 separately permits no list at all.

**Diagnostic obligation:** required.

**Facets:** `EXTERNAL-keyword`, `TYPE-keyword`, `unknown-specifier-repair`.

**Oracle:** The two literal keyword alternatives are tied to complete contexts and their actual
different semantics, with one-token repairs for excluded alternatives.

**Oracle limitation:** Neither order of a distinct TYPE/EXTERNAL pair is forbidden by R869 itself; C895-C897
and overall ordering still apply. The bare and empty-list alternatives belong to
R866/p3, not a fabricated third keyword. No canonical approval or runtime evidence is
supplied.

**Dependencies:** R866;C895-C899;p3;8.5.9;15.4.2.1;15.4.3.5/.6;4.2p2.

### C895: IMPLICIT NONE precedes PARAMETER statements and occurs at most once per scope

**Source:** 8.7 C895, physical PDF141. **Class:** Restriction.

**Definition:** Any IMPLICIT NONE statement in a scoping unit precedes every PARAMETER statement there,
and no more than one IMPLICIT NONE appears in that scope. The rule applies to all NONE
forms, including EXTERNAL-only and empty parentheses. PARAMETER statement is a specific
category; the broader ordering grammar still governs declaration attr-specs and other
specification constructs.

**Diagnostic obligation:** required.

**Facets:** `NONE-before-PARAMETER`, `duplicate-EXTERNAL-only-NONE`, `split-or-duplicate-type-NONE`, `valid-single-NONE-and-order-source`, `separate-scope-boundary`.

**Oracle:** A complete scoped cardinality/order matrix with one-statement deletion/move repairs and
precise attribution. The existing PARAMETER and statement-order interpretations retain
their owners.

**Oracle limitation:** No last-statement-wins or separate-duty exception permits two NONE statements. A generic
missing declaration, missing module or ambiguous type error is not automatically this
ordering/count cause. Numbered reporting need not be fatal, in English or labelled C895.

**Dependencies:** 3.120;5.1R504-R506;5.3.2Tables5.1-5.2;8.6.11R854/S8.6.11-001;R866/C896/C897;p3-p4;11.1.4R1109;4.2p2.

### C896: A NONE specifier is not repeated within one IMPLICIT statement

**Source:** 8.7 C896, physical PDF141. **Class:** Restriction.

**Definition:** The same implicit-none-spec occurs at most once in a given implicit-stmt. Repeated TYPE
and repeated EXTERNAL are distinct finite witnesses of the same prohibition. The rule
does not prohibit one occurrence of each keyword, and it is not C895's count of separate
statements.

**Diagnostic obligation:** required.

**Facets:** `repeated-TYPE`, `repeated-EXTERNAL`, `distinct-specifier-controls`.

**Oracle:** One complete statement and a single repeated list item, with a source-minimal deletion
control and independently valid typing/procedure context.

**Oracle limitation:** Specifier cardinality is not a reason to force a fatal exit or printed rule code.
Full-message/live-origin predicates must exclude source echoes, unsupported facilities
and unrelated errors. No compiler observation or approval is created.

**Dependencies:** R866/R869;C895/C897/C899;p3;4.1.3R401;4.2p2.

### C897: A null-type-map NONE form excludes other IMPLICIT statements in its scope

**Source:** 8.7 C897, physical PDF141. **Class:** Restriction.

**Definition:** If NONE includes TYPE or has no implicit-none-spec list, no other IMPLICIT statement is
permitted in that scoping unit. The no-list branch includes NONE(). EXTERNAL-only does
not satisfy this antecedent, but its coexistence with ordinary mapping statements still
obeys C895, p2-p4 and statement order.

**Diagnostic obligation:** required.

**Facets:** `plain-NONE-plus-map`, `empty-NONE-plus-map`, `TYPE-NONE-plus-map`, `EXTERNAL-only-coexistence`, `scoping-and-overlap-source`.

**Oracle:** Exact TYPE/no-list antecedents and a single controlled additional statement in a
complete scope, with a statement-deletion repair and a separately valid EXTERNAL-only
boundary.

**Oracle limitation:** No generic ban on all statements containing NONE is inferred. Source scope, statement
category, default/null typing and procedure duty are distinct; unsupported or unrelated
output is not causal evidence. No new native result or review is supplied.

**Dependencies:** R866/R869;C895/C896/C899;p2-p4;3.120;5.1/5.3.2;14.2.2;19.5.1.4;4.2p2.

### C898: A letter range has a strictly alphabetically later second endpoint

**Source:** 8.7 C898, physical PDF141. **Class:** Restriction.

**Definition:** When the minus and second letter are present, the second letter follows the first
alphabetically. Equal endpoints and reverse ranges are not the admitted range form. A
single letter has no second-endpoint obligation, and letter case equivalence does not
create a different alphabet.

**Diagnostic obligation:** required.

**Facets:** `descending-range-exclusion`, `equal-endpoint-exclusion`, `ascending-range-control`, `case-and-expansion-source`.

**Oracle:** One actual range in a complete type-map context, with single-endpoint or suffix-deletion
repairs and source-defined alphabetic order.

**Oracle limitation:** The range is not a pair of character values or processor-code integers. A future exact
diagnostic needs complete source/control and actual origin qualification; no universal
wording, fatal status or printed C898 is required.

**Dependencies:** R868;p2;6.1.2p1-p3;S8.7-001;4.2p2.

### C899: NONE(EXTERNAL) requires an explicit interface or explicit EXTERNAL for the stated procedure scopes

**Source:** 8.7 C899, physical PDF141. **Class:** Restriction.

**Definition:** With the EXTERNAL NONE specifier, an external or dummy procedure name in that scoping
unit, a contained subprogram or a BLOCK construct has an explicit interface or is
explicitly declared EXTERNAL. The two routes are alternatives. Data type declaration
alone is not EXTERNAL, and the condition is not selected by NONE(TYPE) or bare NONE
alone. Actual procedure/result/data roles and the separate interface obligations remain
canonical.

**Diagnostic obligation:** required.

**Facets:** `local-external-function`, `local-external-subroutine`, `dummy-procedure-role`, `explicit-interface-alternative`, `procedure-declaration-route`, `contained-subprogram-propagation`, `BLOCK-propagation`, `nonexternal-and-self-name-boundaries`.

**Oracle:** Complete provider/caller/formal-procedure contexts with one missing explicit-EXTERNAL or
interface route, actual role resolution and source-minimal repairs. Scope propagation,
interface alternatives and data typing are checked independently before a report is
attributed to C899.

**Oracle limitation:** No missing-module/link failure, argument mismatch, undeclared data value, intrinsic-name
assumption or unrelated parser error is accepted as this condition. Reporting can be
nonfatal and need not use particular English or C899. Actual f2018 acceptance is not
f2023 corroboration, and no current fixture, compiler observation or approval is
created.

**Dependencies:** R866/R869;8.5.9C842-C844/p1-p2;8.8;11.1.4R1109;14.2.1-.3;15.2.2.1-.5;15.4.2.1/.2;15.4.3.2/.5R1511/.6R1512;15.6.2.2;19.3.1/.3;19.5.1.4;4.2p2.

### S8.7-001: A letter belongs to at most one implicit specification in a scoping unit

**Source:** 8.7 p2 final sentence, physical PDF141. **Class:** Restriction.

**Definition:** The same letter is not specified as a singleton or included in a range more than once
across all IMPLICIT statements in one scoping unit. Inclusive expansion and case
equivalence are applied before checking membership. Equal type/kind/length mappings do
not make duplicate specification permitted. This is a prose restriction separate from
C898 and the NONE cardinality rules.

**Diagnostic obligation:** not-required.

**Facets:** `duplicate-single-letter`, `overlapping-ranges`, `cross-statement-overlap`, `identical-mapping-not-exempt`, `distinct-scope-and-unmentioned-defaults`.

**Oracle:** A bounded original-source membership calculation over complete actual scopes and valid
minimally changed controls. It constrains permitted programs, not a new runtime map
interpreter or an unconditional rejection mandate.

**Oracle limitation:** Prose shall is not automatically a numbered diagnostic requirement. Do not add
invalid/reject fixtures without a repository-supported and independently justified
diagnostic-policy/evidence basis. C898, C895-C897 and established canonical source
owners remain separate; no execution or completion credit is supplied.

**Dependencies:** 8.7p2/p3;R866-R868;C895-C898;6.1.2p3;3.120;4.1.2/4.2;19.5.1.4.

### S8.7-002: Implicit declaration uses a prior explicit mapping or the applicable default mapping

**Source:** 8.7 p4 second sentence, physical PDF141. **Class:** Restriction.

**Definition:** The first-letter mapping used for an implicitly declared data entity is established by a
prior IMPLICIT statement or is the applicable default mapping. This does not demand an
explicit type declaration for every entity and does not replace p4's nonnull/role
exemptions or its FUNCTION-prefix precedence. Subsequent DATA/PARAMETER
declaration-confirmation rules retain their existing owners.

**Diagnostic obligation:** not-required.

**Facets:** `prior-explicit-map`, `default-map-route`, `late-nondefault-map-source`, `explicit-and-canonical-boundaries`.

**Oracle:** Establish the actual implicit-declaration event, first-letter mapping, prior/default
route and exempt entity roles from complete source before choosing an evidence class.
Finite source/interface plans are not fabricated passing runtime tests.

**Oracle limitation:** This prose obligation does not impose mandatory fatal reporting. A source-only/control
relation or explicitly justified policy is required before any invalid diagnostic
fixture. Type selection does not initialize values, certify interfaces, change literal
kinds or discharge real-BOZ/processor-profile conditions. All current source, case,
link, inventory and baseline records remain unrenewed.

**Dependencies:** 8.7p3/p4;R866/R867;5.1/5.3.2;5.4.3;7.3.2.1C710;8.2;8.6.7S8.6.7-002;8.6.11S8.6.11-001;10.1.11p6;15.6.2.2p3-p4;19.3.3;19.5.1.4;4.1.2/4.2.

<!-- END GENERATED 8.7 -->
