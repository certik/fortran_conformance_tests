# Fortran 2023 8.4: Initialization

**INDEPENDENTLY SOURCE-REVIEWED; SELECTED FIXTURES ADDED.** Ten effect facets now have
runtime fixtures; remaining facets stay pending, with no fixture approvals. Source/inventory adjudication is recorded in
`doc/source_audits/batch_027.json`.
`doc/catalogues/initialization_8_4.json` holds the complete finite plans,
conditions, duty classifications and reciprocal source accounting.

Source: checksum-pinned J3/24-007, December 18, 2023, 688 pages, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
Original physical PDF119, printed105, starts at the 8.4 heading and stops
before 8.5. The section hash is
`cb9cc1a678e1fa74fef7967b9b22c2689422cf869e845c40385dfd014553bfbd`.
All three original paragraph hashes were recomputed from the
pinned PDF; the original body text stays in session artifacts.

| Original unit | PDF119 lines | Accounting |
| --- | --- | --- |
| `p1` | 11-18 | Non-PARAMETER variable definition; qualified DATA permission; initial-value effect; one-initialization and array-shape/order restrictions |
| `p2` | 19-20 | Initial disassociation versus association with an eligible initial data target |
| `p3` | 21-22 | COMMON-qualified SAVE implication and permission to confirm it explicitly |

Three base units have twenty-seven fine subdivisions and thirty accounting
rows. Five append-only local S requirements have thirty-five facets; ten effect facets
now have executable fixtures and the rest remain pending. The definition and qualified permissions do not become no-op
programs. Neither prose restriction is assigned a mandatory diagnostic
policy; their nonconforming contrasts remain documentary.

| Qualification | Required limit |
| --- | --- |
| DATA and default initialization | Keep the original derived-type/default-initialization exclusion. The narrower nonpointer wording in 8.6.7p2 does not itself waive another rule. No default-derived pointer is claimed as a valid DATA control without independent cross-role review. |
| Occurrence and identity | Explicit declaration/DATA initialization differs from default initialization and executable assignment. Scope-specific variables sharing a name are distinct; disjoint subobjects differ from overlap. Whole-program COMMON contrasts retain the separate BLOCK DATA restrictions. |
| Order | DATA needs prior array properties and typing confirmation; later DIMENSION does not automatically repair an initialized declaration. A confounded rank/type error is not a shape-order diagnostic oracle. |
| Numeric domains | Symbolic INTEGER kinds and small representable values avoid KIND-code narrowing. REAL/CMPLX approximations and REAL BOZ representations need actual independent oracles; no folklore precision, bits or tolerance. DATA BOZ receivers remain INTEGER. |
| Pointer state | Bare intrinsic NULL in null-init differs from general NULL(MOLD=...) and initial data targets differ from procedure targets. Check status before payload; never inspect unavailable bounds or deferred length. Zero-size targets need the one-argument association-status oracle, not two-argument target-identity truth. |
| SAVE | Retention depends on the actual entity and lifetime. Initializing part of an array does not define its other parts. Saving a pointer does not save an ephemeral target; COMMON has other SAVE routes and active-scope conditions. |
| RANK and source-use | No direct constructor RANK inquiry, fixed-destination rank proxy or phantom graph credit. Any separate constructor-rank witness needs a valid assumed-rank dummy data object. |

Existing C770 and component-default initialization cases keep their primary
owners, source files, IDs and roles. They are dependencies, not relabelled
standalone initialization effects. The frozen 8.1/8.2 source packet and its
six C801/two-review-key staleness evidence are untouched. The original
author packet renewed no receipt. Main registration explicitly renews the
source-context inventory without changing any case or link approval.

The definitions below are generated with `Registry.render(write=True)`
for the owned view only. Complete per-facet plans are in the catalogue.

<!-- BEGIN INITIALIZATION FIXTURES -->
## Initialization runtime observations

Ten complete run/effect/f2023 programs cover six declaration-initializer facets, one pointer target-initialization facet and three implied-SAVE facets. Every asserted initialized value uses a distinctive nonzero, nonblank or .TRUE. sentinel; no fixture expects 0, 0.0, .FALSE. or a blank string as the initialized value. Character fixtures assert LEN explicitly, and array fixtures use nonunit lower bounds; rank-two arrays use distinct extents and explicit LBOUND/UBOUND checks.

Each source has exact completion output plus wrong-oracle, input-literal and initializer-removal mutation plans. The pointer and SAVE initializer-removal mutants are sensitivity probes, not portable conforming programs with defined no-initializer values. `enum-and-enumeration-values`, `numeric-representation-source-use`, null/array/deferred-character pointer cases and the remaining SAVE/source-use facets remain pending.
<!-- END INITIALIZATION FIXTURES -->

<!-- BEGIN GENERATED 8.4 -->

### S8.4-001: A declaration constant initializer establishes the initial value

**Source:** 8.4 p1, physical PDF119, printed105, lines13-16, with lines11-13 context **Class:** Effect.

**Definition:** For the eligible non-PARAMETER variable with equals constant-expression initialization,
the variable is initially defined from that expression. When needed,
intrinsic-assignment conversion supplies a value agreeing with the variable's type, type
parameters and shape. This is an initial-state interpretation, not a repeated executable
assignment on every procedure entry, a pointer-association operation or a waiver of
constant-expression and receiver conditions.

**Diagnostic obligation:** not-required.

**Facets:** `scalar-integer-and-logical`, `integer-kind-conversion`, `character-length-conversion`, `scalar-array-expansion`, `array-values`, `derived-explicit-override`, `enum-and-enumeration-values`, `numeric-representation-source-use`.

**Oracle:** Initial defined scalar, character and array values are compared with independently
derived finite literals; parameter/shape checks accompany values where necessary. The
conversion semantics come from the original standard, never a second execution of the
same conversion or compiler consensus. Type-family plans retain their specific
conformance and constant-expression premises.

S8.4-001 declaration-initializer runtime fixtures: six complete run/effect/f2023
programs observe declaration initializers before any executable assignment to the
initialized variables. The scalar case checks INTEGER -31417 and a .TRUE. LOGICAL
branch; the pending .FALSE. subcase from the original plan is deliberately not used as
an asserted initializer sentinel. The integer-kind case uses SELECTED_INT_KIND(18) and
checks default-to-selected -31417 plus selected-to-default 2719, never a numeric
KIND-code oracle. The character case checks LEN explicitly while observing truncation of
'Zq7R' to LEN 2 as 'Zq' and padding of 'Bx' to LEN 5 with three blanks; the load-bearing
nonblank source characters reject a zero/blank-fill implementation. The scalar-array
case uses INTEGER a(-3:-1)=-24681 and b(5:6,-2:0)=13579, checking LBOUND/UBOUND and
every element, with rank-two extents 2 and 3. The array-value case uses v(4:6)=[2,3,5],
checking nonunit bounds and all elements. The derived case declares a component default
-111 and an object explicitly initialized by sample(2719), then observes 2719 so default
initialization alone cannot pass. Expected values are finite literals hand-derived from
8.4 p1 and intrinsic-assignment conversion; no compiler consensus, storage layout,
TRANSFER or address oracle is used. Wrong-oracle, input-literal and initializer-removal
mutations bind complete-parent byte spans.

**Oracle limitation:** Unimplemented facets remain pending. No real/complex exactness, floating tolerance,
optional kind, native representation or REAL BOZ value is invented. C808 excludes
dummy/result/automatic/ALLOCATABLE and the specified COMMON contexts; C811 distinguishes
equals from pointer initialization. A successful declaration is not execution evidence,
and initial values are not reimposed after every executable redefinition.

S8.4-001 declaration-initializer fixture boundaries: only scalar-integer-and-logical,
integer-kind-conversion, character-length-conversion, scalar-array-expansion,
array-values and derived-explicit-override are represented. The length-zero character
subcase from the original plan is not represented because deleting its initializer
leaves no load-bearing character value to observe. The scalar logical coverage uses
.TRUE. only; no case asserts an initialized .FALSE. value because that would be a
vacuous default-fill sentinel under this packet's non-vacuity rule.
enum-and-enumeration-values and numeric-representation-source-use remain pending. The
fixtures do not cover real/complex approximation, BOZ representation, nondefault
character kinds, ALLOCATABLE entities, PARAMETER receivers, pointer initialization,
default component initialization as an owner, diagnostics or repeated initialization.

**Dependencies:** 8.2 R805/C808/C811 andp4; 8.5.13; 10.1.12; 10.2.1.2 Table10.8 and10.2.1.3
Table10.9/p5/p11/p15; 7.4.3.1; 7.5.4.6p6 and7.5.10; 7.6.1/.2; 7.7 C7119/7.8 C7126-C7127;
8.6.7p11; 16.9.53/16.9.110/16.9.172/16.9.181; 19.6.3.

### S8.4-002: A variable or part has at most one explicit initialization

**Source:** 8.4 p1, physical PDF119, printed105, lines16-17 **Class:** Restriction.

**Definition:** The same variable or part of it cannot receive explicit initialization more than once in
a program. Entity identity and overlap matter, not just spelling or equality of supplied
values. Disjoint parts and distinct variables do not become repetitions merely because
they occur in several statements or share a local name. Executable assignment and the
permitted overriding of default initialization are different mechanisms.

**Diagnostic obligation:** not-required.

**Facets:** `declaration-and-data-contrast`, `repeated-data-contrast`, `whole-and-part-contrast`, `overlapping-subparts-contrast`, `disjoint-parts-admission`, `pointer-initialization-contrast`, `distinct-entity-admission`, `program-scope-source-use`.

**Oracle:** Otherwise-conforming finite source contrasts with focused minimal repairs and positive
admissions. A future diagnostic execution needs a genuine independent numbered causal
owner or an explicitly authorized policy; the prose restriction alone does not require a
compiler to reject or report.

**Oracle limitation:** No policy, invalid runtime, undefined-value trap or byte-overlap model is authored. A
future reporter must identify the actual initialized entity/part and
repeated-initialization relation at the relevant statements; generic duplicate-type,
DATA-count, wrong-kind, missing-END or unsupported-facility errors cannot be credited.
No imposed order among permitted independent initializations.

**Dependencies:** 4.2; 5.4.3.2.1; 7.5.4.6p6-p8; 8.2 C808/C811-C813; 8.6.7p1-p10 andC879/C880/C887/C888;
14.3p2-p5; 19.6.3/.5.

### S8.4-003: An initialized array has its shape specified in the permitted context

**Source:** 8.4 p1, physical PDF119, printed105, lines17-18 **Class:** Restriction.

**Definition:** For an array variable being explicitly initialized, its shape is specified in the type
declaration or in a preceding attribute specification statement in the same scoping
unit. This does not permit shape inference from an initializer as a replacement for a
required variable declaration, retroactive repair by a later attribute statement, or a
shape specification for a different entity in another scope. DATA has additional
prior-property requirements.

**Diagnostic obligation:** not-required.

**Facets:** `entity-shape-admission`, `statement-dimension-admission`, `prior-attribute-admission`, `late-attribute-source-contrast`, `same-scope-source-use`, `data-order-source-use`.

**Oracle:** Conforming compile admissions and original-source order/identity contrasts. No runtime
effect or mandatory diagnostic is inferred from syntactic admission under this
unnumbered restriction.

**Oracle limitation:** The late-specification contrast may intersect other shape/type rules and is not claimed
as an implemented isolated negative. No new diagnostic policy, assumed shape inference,
pointer broadcasting, RANK([...]) probe or fixed-rank-destination proxy is introduced.

**Dependencies:** 8.2 R801/R803/C808 andp4; 8.5.8; 8.6.7p3 and8.6.8; 8.7; 10.1.11/.12 ordering;
16.9.171p3; 5.4.3.2.1/.3,6.2.3 and9.2.

### S8.4-004: Pointer initialization establishes the specified association status

**Source:** 8.4 p2, physical PDF119, printed105, lines19-20 **Class:** Effect.

**Definition:** A null-init establishes initial disassociation; an initial-data-target establishes
initial association with that target. These effects do not allocate anything, define an
arbitrary target value, or authorize a target incompatible with the pointer. The
standalone declaration-initialization role is distinct from component default
initialization and from the initial-proc-target route for procedure pointers.

**Diagnostic obligation:** not-required.

**Facets:** `null-scalar`, `null-array`, `saved-scalar-target`, `saved-array-and-element-targets`, `deferred-character-target`, `data-versus-procedure-source-use`.

**Oracle:** Defined association-status inquiries followed only where legal by defined
target/parameter observations, with an independent target-update alias check. C770
static lifetime and C812 compatibility are prerequisites, not results inferred from
compiler acceptance.

S8.4-004 pointer target-initialization runtime fixture: one complete run/effect/f2023
program initializes an INTEGER POINTER to a saved module TARGET whose declaration value
is -22231. It first requires ASSOCIATED(p,target_value), then reads -22231, changes the
target to -22230 and reads -22230 through the pointer. This distinguishes association
from a one-time value copy without TRANSFER, LOC, C_LOC or address comparison. The
target values are distinct nonzero sentinels; the initializer-removal mutation is a
sensitivity check on the nonconforming mutant and is not used as a portable oracle for
undefined pointer status.

**Oracle limitation:** No negative twin, unavailable pointer inquiry, dangling target, numeric address or
allocation claim. A saved pointer does not extend an unsaved target's lifetime.
ASSOCIATED(pointer,target) has additional nonzero-size/storage-sequence premises and is
not interchangeable with the one-argument status inquiry. Existing C770 and
component-default programs remain unchanged and cannot be relabelled as newly executed
standalone declaration effects.

S8.4-004 pointer target-initialization fixture boundaries: only saved-scalar-target is
represented. Null pointer initializers, array and element targets, deferred-length
character targets and DATA/procedure-pointer source-use remain pending because this
packet does not create a portable no-initializer counterfactual for undefined
association status. The valid parent queries association only while the pointer is
declaration-initialized and defined. It does not claim target lifetime extension beyond
the saved module target or any allocation/storage-address behavior.

**Dependencies:** 5.4.4/5.4.5/5.4.9; 7.5.4.6p2/R744/C770; 8.2 C811-C813; 8.5.14/.16; 8.6.7p9; 15.4.3.6p6;
16.9.155 NULL and16.9.20 ASSOCIATED; 19.5.2.3-.5 and19.6.3/.4.

### S8.4-005: Explicit initialization outside COMMON implies SAVE

**Source:** 8.4 p3, physical PDF119, printed105, lines21-22 **Class:** Effect.

**Definition:** Explicit initialization of a variable outside COMMON gives it SAVE; an explicit
specification may confirm this implication. SAVE's retention semantics and
target-lifetime exceptions remain those of8.5.16 and Clause19. The COMMON exclusion does
not assert that a COMMON object can never have SAVE from another route. PARAMETER
entities, component default initialization and procedure-pointer initialization retain
their different categories and defining rules.

**Diagnostic obligation:** not-required.

**Facets:** `subprogram-retention`, `block-retention`, `data-part-retention`, `saved-pointer-live-target`, `allocated-component-retention`, `common-and-implicit-save-source-use`, `default-versus-explicit-source-use`.

**Oracle:** Multiple executions with exact independently expected retained values/status, not a
successful single call or a storage-address comparison. All observations occur while the
relevant data and association states are defined; the finite program counts expose
omitted second visits.

S8.4-005 implied-SAVE initialization runtime fixtures: three complete run/effect/f2023
programs execute the same initialized entity more than once. The subprogram case has
local INTEGER kept=-31417, returning -31417 on the first call and -31416 after the first
call increments it. The BLOCK case executes one textual BLOCK twice and observes -27182
then the retained -27181. The DATA-part case initializes only a(-2) to -12345 by DATA in
a local array a(-2:-1), defines a(-1)=2468 before any read, and on the second call
observes retained -12344/2468. Each case uses exact visit counts and independent caller
snapshots so a reinitializing implementation, a single-call program or an endpoint-only
check cannot pass. The array DATA case checks nonunit bounds and makes clear that the
uninitialized part is first defined before observation.

**Oracle limitation:** Unimplemented plans remain pending; selected facets below are genuine runs. Do not infer
physical memory clearing or demand a trap for an unsaved variable; do not preserve a
pointer's status by ignoring the target-undefinition exceptions at RETURN/BLOCK exit.
DATA/default-derived qualifications remain recorded separately. Explicit initialization
is incompatible with the excluded C808/C880 entities; permitted explicit SAVE
confirmation is not a second initialization.

S8.4-005 implied-SAVE fixture boundaries: only subprogram-retention, block-retention and
data-part-retention are represented. saved-pointer-live-target,
allocated-component-retention, common-and-implicit-save-source-use and
default-versus-explicit-source-use remain pending. The fixtures do not read an undefined
variable part, infer physical static storage, test COMMON behavior, component default
reinitialization, explicit SAVE confirmation, finalization, recursion, coarrays or
thread interactions. Initializer-removal mutants are negative sensitivity probes rather
than conforming programs with a portable value.

**Dependencies:** 8.2 C808; 7.5.4.6p6-p8 and7.5.10 constant constructor conditions; 8.5.1
C815/8.5.16p1-p4,C861,C862; 8.6.7p4,C880; 8.6.14 C893; 11.1.4 C1108 andNOTE; 15.4.3.6p6
for the distinct procedure-pointer route; 19.5.2.5p1(6)-(7); 19.6.3/.5/.6.

<!-- END GENERATED 8.4 -->
