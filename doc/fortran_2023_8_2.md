# Fortran 2023 8.2: Type declaration statement

**C801 SOURCE/CONTRACT INTEGRATION.** Six retained cases and five
source-minimal compile controls represent six C801 facets;118facets remain
pending. Authorship does not confer source, fixture, case, link or inventory
approval; current adjudications are separate content-bound records.
`doc/catalogues/type_declaration_statements_8_2.json` contains the complete
per-facet finite plans, source conditions and reciprocal accounting.
The definitions below follow the native renderer; `Registry.render()` defaults to check-only.

Source: original checksum-pinned J3/24-007, December 18, 2023, 688 pages,
SHA-256 `7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
Primary scope is physical PDF117-119, printed103-105, ending before the
actual 8.3 heading. The verified section hash is
`d6affa6e58eeb3551bdca653eddc7ad666de72c8c426acf4be5776760ed61e2d`.

| Original units | Source | Treatment |
| --- | --- | --- |
| R801, p1, R802, C801-C803 | PDF117 | Statement envelope; list characteristics; all nineteen attribute alternatives; local uniqueness and BIND conditions |
| p2, R803, C804-C809, R804, C810 | PDF118 | Entity overrides, object/function alternatives, length/initializer/role restrictions |
| R805, R806, C811-C813 | PDF118 | Constant versus pointer initialization, compatibility, intrinsic argument-free null-init |
| p3, p4 | PDF118 | Specific intrinsic definition/permission; generic type no-effect; three conditional nonpointer-initializer predicates |
| `note-unnumbered`, `note-unnumbered.2` | PDF118-119 | One informative NOTE and its actual separately hashed continuation; no fabricated extra note or normative tests |

The nineteen original R/C owners are reused. Four append-only S IDs are
limited to the actual p1/p2 effects, p3 generic no-effect and p4 restriction.
The 25 base units have 102 fine subdivisions and 127 accounting rows.
Six C801 facets are represented;118other facets across the23requirements remain pending.
Definitions, permissions and note examples do not acquire no-op programs.
The actual original text remains in session source artifacts, not copied
into this repository.

Finite negative plans require a complete otherwise-conforming context,
one focused repair and a report tied to the real property, subject and
source location. Reporting capability is not mandatory fatal rejection.
Source echoes, bare punctuation/attribute words, wrong causes, unsupported
facilities, crashes, Internal/ASR failures, resources and generic recovery
cannot establish the selected condition. The unnumbered p4 restriction
does not invent a mandatory diagnostic policy; its negative contrasts
remain source-only until a genuine basis is independently authorized.

| Qualification | Explicit pending limit |
| --- | --- |
| TD-Q01 | C803 procedure-name isolation must satisfy BIND's explicit-interface requirement without duplicate typing or a different object/function defect. An uncalled EXTERNAL name does not remove that requirement. |
| TD-Q02 | C810's proposed initialized EXTERNAL-name contrast needs independent object-slot/procedure-role isolation before execution; PARAMETER is not an invalid data-object category. |
| TD-Q03 | Simultaneous RANK and per-entity array-spec needs reconciliation with 8.5.17 and the shape definitions. No guessed override or rejection oracle. |
| TD-Q04 | Additional distinct kinds, special CHARACTER kinds and REAL BOZ representations need their actual support/representation premises. No KIND codes, widths, byte layouts, new profiles or compiler consensus. |
| TD-Q05 | Source-use relations and genuine coarray effects remain pending; no unapproved source-use infrastructure or compile-only replacement for an effect. |
| TD-Q06 | The five exact per-case contracts and additive valid header resolve the native collection gate. Five source-minimal repairs are supplied. Original grouped receipts stay historical/stale; current source/case/cause approval remains independent. |

Legacy IDs are preserved: `C801_invalid:access-spec`,
`C801_invalid:allocatable`, `C801_invalid:dimension`, `C801_invalid:intent`,
`C801_invalid:parameter` and `C801_valid`, in their two existing
`tests/clause08/C801_*.f90` files. The five invalid programs need per-case
facet/causal-contract bindings, now supplied by the exact-case
sidecar, never a file-level union. Their container bytes remain unchanged.
The valid program remains a real run/effect with only an additive header.
Original grouped evidence remains historical: the invalid group is retired,
while the valid key requires explicit current renewal. No old observation
is relabelled with a new fingerprint.

Initialization-implied SAVE, component default initialization, static
target lifetime, general NULL(MOLD=...), and data/procedure pointer
initialization retain their different canonical contexts. C7119's BOZ
permission does not waive receiver or typed-array consumer conditions.
Existing R703, C770, C815, constructor and assignment witnesses remain
unmodified; mentions and planned source-use do not renew their evidence.

<!-- BEGIN GENERATED 8.2 -->

### R801: Type-declaration statement envelope

**Source:** 8.2 R801, PDF117, printed103, line13 **Class:** Syntax.

**Definition:** A declaration-type-spec precedes a nonempty entity-decl list. The intervening group can
be omitted, can consist of a double colon alone, or can contain comma-prefixed attribute
specifications followed by the double colon. Attributes do not remove their own
entity/scope restrictions. C806 independently requires the separator when an entity has
initialization.

**Diagnostic obligation:** required.

**Facets:** `plain-list`, `bare-double-colon`, `attribute-group`, `attribute-group-needs-colons`, `nonempty-entity-list`, `declaration-type-source-use`.

**Oracle:** Compile admission and two focused grammar/report-control contrasts; source-use
relationships import no execution credit until independently supported. Reporting
capability accepts an ordinary successful or unsuccessful compiler return only with the
intended located report.

**Oracle limitation:** No fixture exists for these plans. Real causal declaration diagnostics, exact source
spans and conforming minimal repairs are required; punctuation fragments, echoes,
facility failures, Internal/ASR errors, resource failures and recovery do not
corroborate the rule.

**Dependencies:** 4.1.2/4.2; 7.3.2.1 R703; 8.2 R802/R803/C806; 8.5 and 8.6. The existing R703 owners are
not redefined.

### R802: Nineteen attribute-spec alternatives

**Source:** 8.2 R802, PDF117, printed103, lines17-35 **Class:** Syntax.

**Definition:** The permitted alternatives are access-spec, ALLOCATABLE, ASYNCHRONOUS, CODIMENSION with
bracketed coarray-spec, CONTIGUOUS, DIMENSION with parenthesized array-spec, EXTERNAL,
INTENT with intent-spec, INTRINSIC, language-binding-spec, OPTIONAL, PARAMETER, POINTER,
PROTECTED, rank-clause, SAVE, TARGET, VALUE and VOLATILE. This is a syntax list, not
permission to use every attribute on every data object or function, or to combine
incompatible attributes. RANK is a DIMENSION-specifying clause, not a separate semantic
attribute.

**Diagnostic obligation:** required.

**Facets:** `access`, `allocatable`, `asynchronous`, `codimension`, `contiguous`, `dimension`, `external`, `intent`, `intrinsic`, `language-binding`, `optional`, `parameter`, `pointer`, `protected`, `rank`, `save`, `target`, `value`, `volatile`.

**Oracle:** Nineteen pending bounded syntax/context plans with canonical semantic ownership.
Admissions are positive controls, not effects. Attribute incompatibilities belong to
their defining C rules; no omnibus negative is inferred from the list.

**Oracle limitation:** A successful declaration does not prove allocation, asynchronous communication,
volatility, SAVE retention or coarray execution. No new profile, companion, compiler
probe or source-use link is included.

**Dependencies:** 8.5.1-C815; 8.5.2-8.5.20 including R807/R808/R814/R828/R829; 8.6 separate statements;
8.2 C801-C813; 15.3/15.4/15.6; 16.8; 18.2.2 C_INT.

### C801: No repeated attribute specification in one declaration

**Source:** 8.2 C801, PDF117, printed103, line37 **Class:** Restriction.

**Definition:** Within one type-declaration statement the same attr-spec may occur at most once. This
statement-local relation is not the same as explicitly specifying an attribute in
separate statements, which remains C815. The finite repeated-specification contrasts use
identical keywords and payloads; mixed PUBLIC/PRIVATE, conflicting INTENT values, and
RANK/DIMENSION interactions are not silently treated as the same isolated condition.

**Diagnostic obligation:** required.

**Facets:** `duplicate-public`, `duplicate-private`, `duplicate-allocatable`, `duplicate-asynchronous`, `duplicate-codimension`, `duplicate-contiguous`, `duplicate-dimension`, `duplicate-external`, `duplicate-intent-in`, `duplicate-intent-out`, `duplicate-intent-inout`, `duplicate-intrinsic`, `duplicate-language-binding`, `duplicate-optional`, `duplicate-parameter`, `duplicate-pointer`, `duplicate-protected`, `duplicate-rank`, `duplicate-save`, `duplicate-target`, `duplicate-value`, `duplicate-volatile`, `distinct-attributes-admission`.

**Oracle:** For each duplicate, one otherwise conforming complete specification context and one
focused deletion repair. A qualified report must identify the repeated
specification/property for the declared entity on its statement; a duplicated source
echo is not a semantic report. Reporting capability need not be fatal.

C801 declaration integration: five existing isolated inputs retain their IDs and
complete bytes. Each receives exactly one facet and an exact-marker,
attribute-repetition diagnose contract, with its full case ID as review key. Five
compile-only positive controls delete only one repeated specification and its comma from
those exact inputs. C801_valid retains its run/effect body and size3/size2 checks, with
only an additive distinct-attributes-admission header. Retained
standard/evidence/profiles are unchanged; new controls use f2023. Error-typed reporting
may return0 or ordinary nonzero; no fatal exit or printed rule code is required.

**Oracle limitation:** Six facets are represented; representation does not confer approval. The other17C801
facets and all101other8.2 facets remain pending. Original grouped evidence remains
historical: the invalid group is retired, while the retained valid review key requires
its own explicit current renewal. Actual cause wording is finite calibration, not
prescribed language. Flang's four located nonfatal duplicate-attribute warnings cannot
be admitted by the existing retained-sidecar schema; preserve their explicit noncredit
without claiming absence of reporting capability or changing warnings/profiles/harness.
Source and inventory adjudication remain separate.

**Dependencies:** 4.2 p2(3); 8.2 R801/R802; 8.5.1 C815 and the individual attribute eligibility
constraints. C801_invalid keeps its five canonical isolated IDs; a file-level union of
their facets would be false coverage.

### C802: A NAME binding specifier limits the declaration list

**Source:** 8.2 C802, PDF117, printed103, lines38-39 **Class:** Restriction.

**Definition:** When a type declaration's language-binding-spec includes NAME=, exactly one entity-decl
is allowed. The condition is presence of the specifier, including an empty or all-blank
value, not whether a nonblank external label results. Without NAME=, this particular
constraint does not limit the list to one entity; all other BIND/data constraints still
apply.

**Diagnostic obligation:** required.

**Facets:** `named-multiple-entities`, `empty-name-multiple-entities`, `unnamed-list-admission`.

**Oracle:** Two NAME-value families of compile reports and minimal single-entity controls, plus a
no-NAME two-entity admission. The causal property is list cardinality under an
explicitly present NAME specifier.

**Oracle limitation:** No binding-label or interoperability failure may substitute for the selected condition.
C_INT is selected symbolically from ISO_C_BINDING; no new processor profile or C
companion is needed or authored.

**Dependencies:** 8.5.5 R808/C818-C820; 18.2.2 and 18.9.2 binding labels; C803 independently excludes
procedures.

### C803: BIND in a type declaration excludes procedure names

**Source:** 8.2 C803, PDF117, printed103, line40 **Class:** Restriction.

**Definition:** A type-declaration statement containing a language-binding-spec cannot have a procedure
name in its entity list. This does not prohibit interoperable procedures declared by
their proper FUNCTION/SUBROUTINE/interface syntax. A procedure with BIND requires an
explicit interface independently of whether it is called.

**Diagnostic obligation:** required.

**Facets:** `procedure-name-exclusion`, `data-name-admission`.

**Oracle:** The exclusion is a numbered reporting relationship, but the negative is not
executable-ready. A future qualified report must establish BIND on a procedure in this
statement role, not missing explicit interface, duplicate type, generic unsupported BIND
or data-variable placement.

**Oracle limitation:** The concrete isolation gate remains open, explicitly separate from the unambiguous
original exclusion. The unrelated valid data admission cannot falsely corroborate a
defective negative. No policy or fallback context is invented.

**Dependencies:** 8.2 R803/C809; 8.5.5 C819/C820; 15.4.2.2 explicit-interface requirements; 15.4.3.2 and
15.6.2.

### R803: Object and function entity-declarator alternatives

**Source:** 8.2 R803, PDF118, printed104, lines5-8 **Class:** Syntax.

**Definition:** The object alternative consists of an object-name followed, in order, by optional
parenthesized array-spec, optional bracketed coarray-spec, optional star char-length and
optional initialization. The other alternative is a function-name with only an optional
star char-length. Names have their actual semantic roles; a result object declared
inside an internal or module function is not automatically a forbidden declaration of
that function name.

**Diagnostic obligation:** required.

**Facets:** `object-suffix-matrix`, `array-coarray-order`, `character-length-order`, `initializer-last`, `function-alternative`, `shape-owner-source-use`.

**Oracle:** Qualified compile admissions and three isolated ordering contrasts, with exact
declared-name/role/source spans and minimal reordering controls. The lexical name and
shape subgrammars remain canonical dependencies.

**Oracle limitation:** Do not turn an illegal function/object role, missing initializer, unsupported coarray
facility or wrong length type into a generic syntax success. Controls must remain
complete and conforming; no runtime outcome is inferred from these admissions.

**Dependencies:** R804-R806/C804-C813; 8.5.6 C822-C829; 8.5.8 R814 and shape constraints; 8.5.17; 15.6.2.2
including C1570/C816.

### C804: Individual star length is CHARACTER-only

**Source:** 8.2 C804, PDF118, printed104, line9 **Class:** Restriction.

**Definition:** An entity's star char-length suffix is available only when the entity has CHARACTER
type. This suffix is a length parameter, not an intrinsic representation-kind selector
or legacy storage-width declaration.

**Diagnostic obligation:** required.

**Facets:** `noncharacter-star-length`, `character-star-length-admission`.

**Oracle:** Noncharacter suffix reports and focused controls distinguish this property from
length-expression type, kind support and missing separators.

**Oracle limitation:** No processor-extension byte-width syntax is treated as standard. No unsupported-kind
report, numeric storage-size observation or runtime no-op is an oracle.

**Dependencies:** 7.4.4.2 R723/C725/C726; 8.2 R803/C805/C809. The CHARACTER length grammar and allowed
contexts retain their defining owners.

### C805: Entity CHARACTER lengths have qualified parameter forms

**Source:** 8.2 C805, PDF118, printed104, line10 **Class:** Restriction.

**Definition:** A type-param-value used in an entity's char-length is a colon, an asterisk or a
specification expression. The expression route is scalar INTEGER and restricted by
10.1.11, with nonconstant expressions confined to the permitted contexts. Colon and
asterisk retain their separate deferred/assumed entity restrictions; this rule does not
universally require constant length and does not permit every entity to use either
special form.

**Diagnostic obligation:** required.

**Facets:** `constant-length-admission`, `nonconstant-specification-admission`, `nonrestricted-local-value`, `assumed-length-contexts`, `deferred-length-contexts`.

**Oracle:** A finite form/context matrix and a nonrestricted-local-value reporting/control pair,
with canonical scalar/type and context relations explicitly separated.

**Oracle limitation:** A local initialized variable is not a named constant. Do not demand a negative-length
trap, use optional/INTENT(OUT) values in the valid specification-expression control, or
inquire about an unavailable deferred length. LEN of a nondeferred CHARACTER length has
different permitted inquiry premises and need not read payload. R723/C725 own
char-length syntax; R724 is CHARACTER literal syntax, not that length grammar.
Special-form eligibility and permission to read an effective argument remain separate.

**Dependencies:** 7.2 C702; 7.4.4.2 R723/C725-C731; 10.1.11 R1029/C1011, p1/p2/p6/p7; 8.3/8.4; 15.5.2.13;
15.6.2.2 and 15.6.4.

### C806: Initialization requires the double-colon separator

**Source:** 8.2 C806, PDF118, printed104, line11 **Class:** Restriction.

**Definition:** An initialization in an entity-decl makes the double colon before the entity list
mandatory, even if there are no attribute specifications. In a declaration that already
has attributes, R801 independently requires that separator.

**Diagnostic obligation:** required.

**Facets:** `initializer-without-attributes`, `all-initialization-routes-source-use`.

**Oracle:** One otherwise-valid initializer-triggered separator contrast with a one-token repair,
and a bounded source-use connection for the three initializer alternatives.

**Oracle limitation:** No broad punctuation or bare 'expected' diagnostic matcher. The source relation and
complete repaired declaration must be independently clear.

**Dependencies:** R801/R805 and C811-C813; 4.2 reporting capability.

### C807: PARAMETER declarations initialize every entity

**Source:** 8.2 C807, PDF118, printed104, line12 **Class:** Restriction.

**Definition:** When PARAMETER appears as an attribute keyword in a type declaration, every entity-decl
in that statement must include initialization. A separate PARAMETER statement is another
canonical route, not an exception permitting a missing initializer in this form.

**Diagnostic obligation:** required.

**Facets:** `missing-member-initializer`, `all-members-initialized`.

**Oracle:** Located missing-per-entity initialization reports with constant-expression controls, not
mandatory nonzero exit.

**Oracle limitation:** No existing C801 PARAMETER-duplication case is re-owned or credited here.
Constant-expression ordering and intrinsic initialization compatibility must
independently hold.

**Dependencies:** 8.5.13, 8.6.11; 10.1.12; R805/C806; S8.2-004.

### C808: Entity categories that cannot have declaration initialization

**Source:** 8.2 C808, PDF118, printed104, lines13-15 **Class:** Restriction.

**Definition:** An object declarator cannot have initialization when it names a dummy argument, a
function result, a named-COMMON object outside BLOCK DATA, any blank-COMMON object, an
allocatable variable or an automatic data object. Only the named-COMMON category has the
BLOCK DATA exception. These are properties of the declared entity itself, not a
recursive ban on a derived object merely because a component is allocatable or
default-initialized.

**Diagnostic obligation:** required.

**Facets:** `dummy`, `function-result`, `named-common-outside-block-data`, `blank-common`, `allocatable`, `automatic`, `named-common-block-data-admission`, `ordinary-derived-admission`.

**Oracle:** Six independently isolated category families, with both array-bound and
CHARACTER-parameter automatic cases, each repaired by removing only declaration
initialization. Positive admissions distinguish the named-COMMON exception and the
entity-versus-component boundary.

**Oracle limitation:** An otherwise invalid BLOCK DATA unit, undefined repaired function result, illegal dummy
initializer type or unsatisfied constructor constant-expression requirement is not a
control. No runtime initialization or implied-SAVE effect is authored under this
restriction.

**Dependencies:** 8.1/8.3 C814/8.4; 8.5.13/8.5.16 C862; 8.10.2 COMMON; 14.3 C1415/C1416; 15.6.2.2; 7.5.10
and 10.1.12.

### C809: Eligible function-name roles in entity declarations

**Source:** 8.2 C809, PDF118, printed104, lines16-17 **Class:** Restriction.

**Definition:** The function-name alternative denotes an external function, intrinsic function, dummy
function, procedure pointer or statement function. This list classifies that grammar
role. It does not ban type declarations for the distinct result objects of internal or
module functions, and it does not turn an ordinary subroutine into a typed function.

**Diagnostic obligation:** required.

**Facets:** `external-function`, `intrinsic-function`, `dummy-function`, `procedure-pointer`, `statement-function`, `result-role-boundary-source-use`.

**Oracle:** Five finite eligible-role admissions and a source-use boundary plan, not five no-op
effects or an invented universal function-definition ban.

**Oracle limitation:** The standard requires reporting an actual numbered violation, but no isolated negative
is claimed ready for the role-boundary plan. All facets are pending; no existing
procedure cases are copied or re-owned.

**Dependencies:** R803/C810; 8.1 p2/p3; 8.5.9/8.5.11/8.5.14; 15.4.3.6, 15.6.2.2 and 15.6.4; 16.8.

### R804: Object-name uses the canonical name syntax

**Source:** 8.2 R804, PDF118, printed104, line18 **Class:** Syntax.

**Definition:** The object-name syntactic category uses name. C810 supplies its data-object role; R603
and Clause6 retain spelling, source-form and name-length conditions.

**Diagnostic obligation:** required.

**Facets:** `canonical-name-source-use`.

**Oracle:** Source-use binding of the name syntax to the object slot; no additional execution credit
or duplicated lexical negative.

**Oracle limitation:** The coordinator's source-use prototype is unapproved and not a dependency of this draft.
No bare alias is promoted to an S no-op.

**Dependencies:** 6.2.2 R603/C601; R803/C810.

### C810: An object declarator names a data object

**Source:** 8.2 C810, PDF118, printed104, line19 **Class:** Restriction.

**Definition:** An object-name in the object declarator denotes a data object. The category includes
constants and variables, so PARAMETER is not a counterexample. Procedure identifiers
have their separate roles even when a type is specified for a function.

**Diagnostic obligation:** required.

**Facets:** `constant-and-variable-admission`, `procedure-in-object-slot`.

**Oracle:** A positive data-category pair and a bounded but not yet approved procedure/object
isolation plan. The procedure definition and declaration roles must be reconciled before
authoring a diagnostic fixture.

**Oracle limitation:** No undefined data, artificial category query or blanket PARAMETER/procedure-pointer
assumption. The candidate is not claimed as an already valid negative/control pair.

**Dependencies:** 3.42 data object; R803/R804/C809; 8.5.9; 15.3/15.6.2.2.

### R805: Intrinsic and pointer initialization alternatives

**Source:** 8.2 R805, PDF118, printed104, lines20-22 **Class:** Syntax.

**Definition:** Initialization has three alternatives: equals with a constant expression, arrow with
null-init, or arrow with initial-data-target. Constant-expression restrictions, the
separate explicit BOZ consumer allowance, pointer status, no-argument intrinsic NULL and
static-target compatibility/lifetime all keep their defining conditions.
Procedure-pointer initialization uses its own applicable declaration grammar, not an
arbitrary R805 data-object slot.

**Diagnostic obligation:** required.

**Facets:** `constant-expression-admission`, `nonconstant-initializer`, `null-admission`, `static-target-admission`, `constant-and-boz-source-use`.

**Oracle:** Three initializer-route admissions and one constant-expression reporting/control
contrast, plus explicitly pending canonical source-use. Actual initial
values/association are governed by 8.4 and are not new local syntax effects.

**Oracle limitation:** No declaration-time procedure call, invalid lifetime target or compiler-accepted BOZ
representation supplies an oracle. The source-only packet contains no executable cases
or newly authorized policy.

**Dependencies:** 10.1.12; 7.7 C7119; 7.8 C7126/C7127; 16.3.3 C1601; 7.5.4.6 R744/C770; C811-C813; 8.4;
15.4.3.6 R1517.

### R806: Null-initializer function-reference syntax

**Source:** 8.2 R806, PDF118, printed104, line23 **Class:** Syntax.

**Definition:** A null-init has function-reference syntax. C813 restricts that reference to
argument-free intrinsic NULL. Other contexts in which a NULL result is permitted do not
thereby become uses of R806 null-init.

**Diagnostic obligation:** required.

**Facets:** `bare-null-reference`, `reused-null-init-source-use`.

**Oracle:** Function-reference structure and source-use roles, with identity/argument negatives
retained by C813.

**Oracle limitation:** A missing-parentheses identifier might be parsed as a target designator, so do not
manufacture a supposedly isolated R806 syntax negative from that ambiguity. Bare-NULL
admissions also satisfy16.9.155 Table16.5: no assumed contextual type parameter
requiring MOLD, or generic/assumed-rank actual-argument context requiring MOLD, is
smuggled into the plan.

**Dependencies:** 15.5.1 function-reference; C813; 7.5.4.6 R743, 15.4.3.6 R1517, and 16.9.155 NULL.

### C811: Initialization operators require opposite pointer status

**Source:** 8.2 C811, PDF118, printed104, lines24-25 **Class:** Restriction.

**Definition:** Arrow initialization requires the declared entity to have POINTER. Equals initialization
excludes POINTER. This does not reinterpret equals as association, and it is not scalar
value broadcasting into a pointer target.

**Diagnostic obligation:** required.

**Facets:** `arrow-needs-pointer`, `equals-forbids-pointer`, `canonical-pointer-status-source-use`.

**Oracle:** Two opposite pointer-status reporting relations with one-attribute repairs and complete
declarations. Numeric assignment/conversion diagnostics are not interchangeable with the
selected operator/status condition.

**Oracle limitation:** No invalid pointer value, undefined target, or intentionally mismatched NULL MOLD is
used. Ordinary0/nonzero reporting capability, not fatal/code-specific behavior, is the
planned expectation.

**Dependencies:** R803/R805; 8.5.14; C812/C813; 15.4.3.6.

### C812: Initial data targets satisfy full initialization compatibility

**Source:** 8.2 C812, PDF118, printed104, lines26-27; 7.5.4.6 p2, PDF96 **Class:** Restriction.

**Definition:** When an initial-data-target is supplied, the object and target satisfy the
data-pointer-initialization relation: the pointer is type compatible with the target,
ranks agree, every nondeferred pointer type parameter equals the corresponding target
parameter, and a CONTIGUOUS pointer has a contiguous target. Deferred parameters are not
a fixed-parameter mismatch. C770 independently requires an eligible saved static target
and constant designator expressions.

**Diagnostic obligation:** required.

**Facets:** `type-mismatch`, `supported-kind-mismatch`, `rank-mismatch`, `fixed-length-mismatch`, `contiguity-mismatch`, `compatible-and-deferred-admissions`.

**Oracle:** Separate type, supported-kind, rank, fixed-parameter and conditional-contiguity
contrasts. Every negative has a focused repair and must report its actual differing
property for the correct pointer/target relation.

**Oracle limitation:** All facets are pending. No arbitrary KIND code, unsupported-kind substitution, unsaved
target, vector subscript, nonconstant designator or out-of-lifetime target can be used
to make a misleading negative/control. C770's existing programs remain unchanged and
unowned here.

**Dependencies:** 7.3.3 type compatibility; 7.5.4.6 p2/R744/C770; 8.5.7/8.5.14/8.5.16; 9.5.4 contiguity;
19.5.2.

### C813: Null-init is argument-free intrinsic NULL

**Source:** 8.2 C813, PDF118, printed104, line28 **Class:** Restriction.

**Definition:** The function reference used specifically as null-init denotes the intrinsic NULL
function and has no actual arguments. This restriction follows the R806 syntax where
reused, including applicable component and procedure-pointer initialization. It does not
forbid MOLD on a general NULL expression in a context governed by other syntax.

**Diagnostic obligation:** required.

**Facets:** `mold-argument-excluded`, `nonintrinsic-reference-excluded`, `no-argument-and-general-null-source-use`.

**Oracle:** Intrinsic identity and no-actual-arguments are different report predicates and different
focused repairs. General MOLD contexts are qualified source-use, not invalid twins.

**Oracle limitation:** Intrinsic identity is not just matching the source spelling NULL. The user-function
contrast remains subject to independent interface/role isolation; no selected negative
is claimed implemented or approved.

**Dependencies:** R806; 16.9.155 NULL and Table16.5; 7.5.4.6 R743; 15.4.3.6 R1517; 15.6.2.2 pointer result
definition.

### S8.2-001: Declared characteristics apply to the entity list

**Source:** 8.2 p1, PDF117, printed103, lines14-16 **Class:** Effect.

**Definition:** The declaration determines the list entities' declared type and type parameters from its
declaration-type-spec, with an individual CHARACTER star-length replacing the length for
that entity. Other entities keep the statement's length and the kind is not changed by
an individual length. Canonical assumed/unlimited and deferred/assumed-parameter forms
retain their special interpretations.

**Diagnostic obligation:** not-required.

**Facets:** `declared-type-across-list`, `kind-and-pdt-parameters`, `entity-character-length`.

**Oracle:** Independent small INTEGER values, explicit observer type contracts and exact
CHARACTER/PDT parameter inquiries. Each list member is checked against source-derived
constants, not only against another member that could share the same error.

**Oracle limitation:** No compiler probing or effect fixture is included. KIND identifiers need not be1/4/8 or
fit another selected kind. Unsupported features must not later downgrade a planned run
to a compile-only control.

**Dependencies:** 7.2; 7.3.2.1 R703 and assumed/unlimited qualifications; 7.4.4.2 length interpretation;
7.5.3 type parameters; 16.9.118 KIND/16.9.122 LEN; 19.6 definition.

### S8.2-002: List attributes and individual shape specifications

**Source:** 8.2 p2, PDF118, printed104, lines1-4 **Class:** Effect.

**Definition:** The statement's attribute keywords apply to its listed entities. An entity's array-spec
can specify or replace the DIMENSION specification, and its coarray-spec can specify or
replace CODIMENSION. The resulting forms still satisfy their independent shape, coshape
and entity restrictions. The interaction of an explicit RANK clause with an entity
array-spec is not resolved by treating RANK as just another freely overridden keyword.

**Diagnostic obligation:** not-required.

**Facets:** `list-attributes`, `entity-array-override`, `entity-coarray-override`, `rank-clause-interaction-source-use`.

**Oracle:** Defined values and independent extent/corank-lower-bound observations for the admitted
ordinary forms, plus an explicitly unresolved source-use interaction rather than a
guessed result.

**Oracle limitation:** An entity coarray declaration is not proof of multi-image behavior. No new coarray
profile/companion or reduced compile-only replacement is supplied. RANK's additional
eligibility and shape semantics remain canonical.

**Dependencies:** 8.5.1 C815; 8.5.6 C822-C829; 8.5.8 including R814 and rank-clause references; 8.5.17
R829/C863/C864; 16.9.194 SIZE/16.9.120 LCOBOUND; 19.5.2.

### S8.2-003: A generic intrinsic name's type declaration has no effect

**Source:** 8.2 p3 final sentence, PDF118, printed104, lines30-31 **Class:** Effect.

**Definition:** A type specified for a generic intrinsic function name in a type-declaration statement
does not change the generic reference's result type or parameters. The actual generic
intrinsic specification still determines them. This no-effect statement is about the
type specification, not arbitrary other attributes, shadowed user procedures or
restricted-specific actual-procedure roles.

**Diagnostic obligation:** not-required.

**Facets:** `generic-type-no-effect`.

**Oracle:** 16.9.110 says INTEGER input returns that INTEGER value, with default INTEGER kind when
KIND is absent. The observer's explicit INTEGER interface and literal7 value jointly
detect an incorrectly type-altered generic result.

**Oracle limitation:** This planned effect is nonempty and remains a run even if a processor rejects the
permitted declaration. DSIN/specific-intrinsic type permission is separately
definition/permission accounting, not this effect or a new wrong-type diagnostic policy.

**Dependencies:** 8.5.11; 16.8 Tables16.2/16.3, PDF374-376; 16.9.110, PDF421-422; explicit argument
association in 15.5.

### S8.2-004: Nonpointer initializer type, parameter, rank and shape conditions

**Source:** 8.2 p4 and three list items, PDF118, printed104, lines32-36 **Class:** Restriction.

**Definition:** For a nonpointer entity with initialization, type and type parameters conform as for
intrinsic assignment. An implied-shape entity requires an initializer of the same rank.
Otherwise the initializer is scalar or has exactly the entity's shape. Equal element
counts do not establish equal shapes. These are prose restrictions, not a new universal
mandatory reporting policy. Initialization values and conversion are interpreted by
8.4/10.2.1.3.

**Diagnostic obligation:** not-required.

**Facets:** `type-conformance-source-use`, `numeric-admission`, `character-kind-and-length-admission`, `derived-parameters-source-use`, `enum-enumeration-source-use`, `implied-shape-rank`, `other-scalar-admission`, `other-same-shape-admission`, `other-shape-source-contrast`, `boz-consumer-source-use`.

**Oracle:** Complete conforming compile admissions for the stated predicates and finite
original-source contrasts for their failures. Any future executed initialization effects
require independent small literal/string/shape oracles under8.4 and the actual
conversion owner, not compiler consensus or another copy of the operation.

**Oracle limitation:** No negative execution is authorized under this unnumbered restriction without an
explicit independently reviewed diagnostic basis. Source-only contrasts are plans, not
fixtures. No undefined/absent/unallocated payload, pointer broadcasting, implicit
kind-code conversion or REAL representation guess is used.

**Dependencies:** 8.4; 8.5.8 implied shape and R814; 10.1.12; 10.2.1.2 Table10.8 and CHARACTER/derived
parameter premises; 10.2.1.3 Tables10.9; 7.5.10; 7.6; 7.7 C7119; 7.8 C7126/C7127; 16.3.3
C1601.

<!-- END GENERATED 8.2 -->

## Finite C801 metadata and causal-contract integration

The original six execution IDs remain. Five negative inputs are produced by the existing
`isolated_cases` helper, including its original blank-line padding and marker comments.
The new positive controls delete only the second repeated attribute specification and its
preceding comma/space. They do not reconstruct or simplify the program units.

| Retained negative | Only facet | Original marker | Compile-only repair |
| --- | --- | ---: | --- |
| `C801_invalid:access-spec` | `duplicate-public` | 23 | `C801_valid__c801_declaration_access_spec_control` |
| `C801_invalid:allocatable` | `duplicate-allocatable` | 5 | `C801_valid__c801_declaration_allocatable_control` |
| `C801_invalid:dimension` | `duplicate-dimension` | 10 | `C801_valid__c801_declaration_dimension_control` |
| `C801_invalid:intent` | `duplicate-intent-in` | 15 | `C801_valid__c801_declaration_intent_control` |
| `C801_invalid:parameter` | `duplicate-parameter` | 19 | `C801_valid__c801_declaration_parameter_control` |

* `C801_invalid:access-spec`: Initialized module INTEGER m=1 in the specification part. Delete exactly `, public`.
* `C801_invalid:allocatable`: Local deferred-shape REAL b(:), with its ALLOCATE(b(2)) retained. Delete exactly `, allocatable`.
* `C801_invalid:dimension`: Local explicit-shape INTEGER a(3), with the complete a=1 assignment retained. Delete exactly `, dimension(3)`.
* `C801_invalid:intent`: Scalar INTEGER dummy x with INTENT(IN), unmodified and unread in its complete procedure. Delete exactly `, intent(in)`.
* `C801_invalid:parameter`: INTEGER named constant n=1; its required constant initializer is retained. Delete exactly `, parameter`.

`C801_valid` is only `distinct-attributes-admission`: its complete existing body,
DIMENSION/PARAMETER and ALLOCATABLE/DIMENSION declarations, allocation, definition
and size3/size2 guards are unchanged. It remains run/effect, not an empty compile
substitute or the repair of any negative. Retained effective standard/evidence/profiles
are unchanged; only the five new compile controls declare f2023.

Each negative now has `outcome=diagnose` and its own full-ID review key, deliberately
replacing old reject/group-key semantics. Its sole facet, exact isolated marker line,
observed attribute-repetition cause phrases and exclusions are in
`tests/clause08/C801_invalid.cases.json`. No file-wide facet union is introduced.
Original grouped evidence remains historical. The invalid group is retired, while
the valid key requires explicit current renewal; current bindings need independent review.

C801 is statement-local. C815 and individual attribute eligibility remain prerequisites,
not new coverage. PUBLIC stays in a module specification part; ALLOCATABLE retains its
REAL deferred-shape array and allocation; DIMENSION retains INTEGER shape3 and a=1;
INTENT retains the unchanged INTEGER IN dummy; PARAMETER retains n=1. No mixed
PUBLIC/PRIVATE, INTENT payload, RANK/DIMENSION or other attribute contrast is added.

The required capability under4.2p2(3) is reporting, not mandatory fatal rejection or
printed rule codes. A located, cause-matching error diagnostic can have return0 or an
ordinary nonzero status. Bare keywords, source echoes, unrelated typing/allocation,
recovery, unsupported facilities, Internal/verifier/resource failures and timeouts
do not corroborate repetition. Native wording is not prescribed by the standard.

The frozen calibration records Flang warnings for PUBLIC, ALLOCATABLE, INTENT(IN)
and PARAMETER. They are genuine located repetition reports, but retained sidecars
currently cannot encode `allow_nonfatal`. Their noncredit is preserved as a mechanism
limitation, not absence of reporting capability. No warning flag, profile, shared
harness change or forced reference agreement is used. F2018 results are not promoted
to F2023 qualification of this source packet.

The original author packet excluded its local8.1/8.2index overlay, preserving1972
retained IDs,1966unaffected fingerprints, nine links and the empty SourceUses registry.
Six C801 fingerprints intentionally changed, and five new controls yielded1977cases.
Subsequent registration and source/case/inventory adjudication are coordinator actions,
not generator side effects. Current receipt states must be read from the registry.

`python3 -B tools/generate_c801_declaration_fixtures.py --check` verifies exact generated
inputs, the additive header, sidecar and owned8.2render. Bounded regressions cover
minimal repairs, individual facets, migration, actual markers, causal/nonfatal/failure
predicates and administrative preservation. Independent source/fixture/oracle review
and current-main index/inventory integration remain separate gates.
