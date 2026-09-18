# Fortran 2023 8.9: NAMELIST statement

The authoritative catalogue is `doc/catalogues/namelist_statement_8_9.json`.
Effective source status is `Registry.catalogue_review_state("8.9")`.
This unapproved source-only packet has no fixtures, compiler observations,
profile changes, source uses, canonical links or review renewals. Every new
facet remains pending.

The authority is J3/24-007, December18,2023, 688 physical pages,
SHA-256 `7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The actual section starts on physical PDF145 and ends on146 at8.10.
All11original units are included: p1, R871/R872, C8107-C8109, p2-p5 and
the unnumbered note. Five numbered units were already globally accounted;
the five paragraphs and note add six base units.

## Group and object identity

R871 requires slash-delimited named groups and nonempty object lists.
The comma between group clauses is optional; commas within an object list
serve a different role. There is no unnamed group, double-colon alternative,
rename or inline object declarator. The complete502-head scan finds no
explicit `namelist-group-name` rule, so R402/R603 supplies that name.
R872 instead uses **explicit R903/C903 variable-name**, not assumed R402.

C8107 prohibits a USE-associated name in the group-name position, not a
USE-associated variable as a member or an imported group used for transfer.
A NAMELIST group declared locally can hide a host homonym under19.5.1.4p2;
it is not necessarily continuation of that host's group. Statement scope
and the C1107 BLOCK exclusion remain independent.

C8108 concerns actual assumed-size arrays. A module dummy repaired from
`a(*)` to `a(:)` retains a complete explicit interface; an array element
is not a valid repair because R872 requires the whole variable name.

C8109 concerns **enumeration type**, not interoperable enum type or a
generic integer representation. Its direct-component condition is recursive:
3.30.1/7.5.1p4 continues through nonpointer nonallocatable derived components.
An immediate enumeration-typed component is direct even if that component
has POINTER/ALLOCATABLE; a deeper enumeration behind a component of a
different derived type with POINTER/ALLOCATABLE is a different path.
Direct, ultimate and potential-subobject components must not be conflated.
Every future negative/control keeps the enumeration definitions so a
processor's unsupported type syntax cannot masquerade as this constraint.
Defined I/O supplies no C8109 exception.

## Prose and observation plans

Five append-only S requirements retain the surrounding obligations:

| Requirement | Meaning |
| --- | --- |
| S8.9-001 | Output values follow object-list order |
| S8.9-002 | Repeated object occurrences each contribute their value |
| S8.9-003 | Successive same-scope group declarations concatenate lists |
| S8.9-004 | Type, kind parameters and rank have a permitted established source |
| S8.9-005 | A later declaration confirms prior implicit type/parameters |

P1 defines the group's transfer purpose, retaining12.6/13.11 ownership.
P4 permits membership in multiple groups; its finite admission plan is
not another local S/no-op effect. Repeated group declarations are expressly
permitted, not an accidental C815 duplicate-attribute error.

Output order and multiplicity require actual output observations. A
namelist READ-back can accept reordered input or hide a dropped duplicate,
so round-trip value equality alone is insufficient. Proposed bounded
INTEGER observers need independent literal/name/occurrence expectations,
complete I/O status and completion guards, and wrong-order/omission
sensitivity. No parser or executable is implemented here.

Intrinsic output uses uppercase names and the13.11 structure, but record
lengths, legal whitespace, separators and numeric editing cannot be reduced
to one compiler's pretty-printed text. Repetition compression within an
object, character/DECIMAL/DELIM rules and defined I/O retain separate
conditions. Group declaration does not establish allocation, association,
defined values or permission to transfer opaque/private components.
Under12.6.4.7p2, every allocatable group object must be allocated and every
pointer group object associated at transfer, not just selected input names.
Polymorphic objects and objects with pointer/allocatable ultimate components
require defined I/O; declaration membership does not supply that procedure.

P5 allows genuine USE/HOST routes or previous same-scope/implicit property
establishment. It does not require a new explicit local declaration in every
case, and an actual nonnull implicit mapping can supply a scalar's type and
default kind. Prior rank is distinct from a later DIMENSION declaration.
The later-confirmation condition applies when implicit typing supplied the
type, including its parameters, not to arbitrary prior explicit types.

The note is an incomplete syntax example, not a value oracle. Numbered
reporting remains capability rather than mandatory fatal status or English.
Prose restrictions need an actual numbered/name-scope or explicit policy
basis before negative fixtures. No whole-standard or processor claim follows
from this source accounting.

<!-- BEGIN GENERATED 8.9 -->

### R871: NAMELIST has slash-delimited named groups with nonempty object lists

**Source:** 8.9 R871, J3/24-007, 18 December 2023, physical PDF146. **Class:** Syntax.

**Definition:** NAMELIST is followed by /group-name/ and a nonempty group-object list. Additional
slash-delimited group clauses may follow, each optionally preceded by a comma and each
with its own nonempty object list. There is no unnamed group or double-colon
alternative. R401 supplies the object lists; the complete grammar-head scan finds no
explicit namelist-group-name rule, so R402/R603 supplies that name convention. Actual
objects use R872/R903.

**Diagnostic obligation:** required.

**Facets:** `single-group`, `multiple-groups-with-comma`, `multiple-groups-without-comma`, `name-and-slash-repairs`, `nonempty-object-lists`, `object-comma-repairs`, `shared-object-group-permission`, `scope-order-and-name-source`.

**Oracle:** Complete legal declaration contexts and one-predicate group/list punctuation repairs,
with shared membership admitted and exact group/object roles.

**Oracle limitation:** Numbered reporting is capability, not fixed English, fatal status or printed R871.
Missing types/providers, invalid roles/scopes, unsupported features, source echoes and
native failures do not establish a distinct grammar cause. No output or membership-value
effect follows from compilation alone.

**Dependencies:** 4.1.3R401/R402/p2;6.2.2R603/C601;5.1R504/R513;R872/C8107-C8109;8.9p1/p3/p4/p5;11.1.4C1107;19.5.1.4p2;4.2p2.

### R872: A namelist group object is a whole variable name

**Source:** 8.9 R872, physical PDF146. **Class:** Syntax.

**Definition:** A namelist-group-object is variable-name, using explicit R903/C903 rather than assumed
R402. It names a variable, not a constant, expression, selected component, array
element/section or new array declaration. A whole array name is possible subject to
C8108, C8109 and the prior-property rules. Declaration membership and later
data-transfer eligibility are separate.

**Diagnostic obligation:** required.

**Facets:** `ordinary-variable-names`, `whole-array-not-selector`, `constant-procedure-role-source`, `associated-objects-and-transfer-state-source`.

**Oracle:** Actual variable identities with complete declaration and whole-name controls; canonical
role and transfer-state constraints stay separate.

**Oracle limitation:** A valid identifier does not make a parameter or procedure a variable, and grammar
admission does not prove readable/definable values or I/O support. No fixture, link,
profile or source-use approval is created.

**Dependencies:** 9.2R903/C903;4.1.3p2;6.2.2;C8108/C8109;8.9p5;14.2.2note4;19.5.1.4;12.6.3;12.6.4.7p2;13.11.2/.3/.4.

### C8107: A NAMELIST declaration does not use a USE-associated name as its group name

**Source:** 8.9 C8107, physical PDF146. **Class:** Restriction.

**Definition:** A group name in a NAMELIST statement is not a name accessed by use association. This
does not prohibit USE-associated variables as group objects, nor automatically prohibit
accessing an imported group in an I/O statement. The group-name slot and object-name
slots have different conditions.

**Diagnostic obligation:** required.

**Facets:** `use-associated-group-exclusion`, `renamed-group-exclusion`, `use-associated-object-control`, `host-group-local-identity-source`.

**Oracle:** Complete provider/consumer name-role contrasts with one-name repairs and exact
use/host/local association paths.

**Oracle limitation:** Do not turn this into a ban on using an imported group for transfer or importing group
members. Keyword matching, missing providers and unqualified host-shadow assumptions do
not establish the predicate.

**Dependencies:** 14.2.2p2/p7/note4;19.3.1;19.5.1.4p1/p2(15);8.8C8106;8.9p3/p5;12.6.2.1C1216;4.2p2.

### C8108: Assumed-size arrays are not namelist group objects

**Source:** 8.9 C8108, physical PDF146. **Class:** Restriction.

**Definition:** A namelist group object is not an assumed-size array. Its actual declared role and array
category matter, not the appearance of a star anywhere in the file. This is not a
general ban on arrays, assumed shape or every dummy object, and a selected array element
is not an allowed R872 repair.

**Diagnostic obligation:** required.

**Facets:** `assumed-size-dummy-exclusion`, `assumed-shape-dummy-control`, `star-role-and-other-rank-source`.

**Oracle:** Actual assumed-size dummy versus a minimally repaired explicit-interface assumed-shape
dummy, with rank/type and group syntax unchanged.

**Oracle limitation:** An error in the dummy declaration or unsupported assumed-shape/NAMELIST feature does not
qualify this cause. No call, missing main, undefined value or source-only star
classifier is an effect.

**Dependencies:** 8.5.8.3p1;8.5.8.5p1/R825/C835/C837;8.5.8.6C838;8.5.8.7;R872;8.9p5;15.4.2.2;4.2p2.

### C8109: Enumeration-type variables and enumeration-typed direct components are excluded

**Source:** 8.9 C8109, physical PDF146. **Class:** Restriction.

**Definition:** A namelist group object is neither of enumeration type nor an object having a direct
component of enumeration type. Direct component is the recursive3.30.1/7.5.1p4 concept:
it includes immediate components and continues through nonpointer nonallocatable derived
components. This is not just one level, arbitrary pointer reachability or the distinct
interoperable enum type of7.6.1. C8109 has no defined-I/O exception.

**Diagnostic obligation:** required.

**Facets:** `enumeration-variable-exclusion`, `immediate-enumeration-component`, `recursive-nonpointer-nonallocatable-path`, `component-attribute-boundary`, `pointer-allocatable-hop-boundary`, `enum-versus-enumeration-source`.

**Oracle:** Complete actual F2023 type graphs and source-minimal object-name repairs retaining the
same type support in both programs. Apply the recursive direct-component definition
independently.

**Oracle limitation:** Source support is not compiler support. Rejection at ENUMERATION TYPE before a valid
control compiles cannot prove C8109. Direct, ultimate and potential-subobject components
differ; no object traversal or transfer is implemented.

**Dependencies:** 3.30.1/.2;7.5.1p3-p6;7.5.7.2;7.6.1/.2;R872/9.2C903;12.6.3;12.6.4.7p2;13.11;4.2p2.

### S8.9-001: Namelist output values follow group object-list order

**Source:** 8.9 p2 first clause, physical PDF146. **Class:** Effect.

**Definition:** Values on namelist output appear in the order of the objects in the group's object list.
This is an output-order requirement, not an input-order restriction: namelist input may
use another order or omit objects. Record breaks, value editing and defined I/O retain
their own rules.

**Diagnostic obligation:** not-required.

**Facets:** `distinct-scalar-output-order`, `array-then-scalar-order`, `portable-output-observer`, `whole-parent-sensitivity`.

**Oracle:** Observed complete namelist output with independently established finite values and list
positions, using a source-qualified record observer and complete lifecycle guards.

**Oracle limitation:** No executable or record parser is supplied. Successful WRITE or read-back proves neither
order nor the whole formatting standard; processor-dependent record lengths/widths and
defined I/O must not be narrowed silently.

**Dependencies:** 8.9p1/p3;12.6.2.1C1216/C1217;12.6.3;13.11.2;13.11.3.1p2;13.11.4.1-.3;13.10.4;9.5.3.3;19.6.2.

### S8.9-002: Every repeated group-object occurrence contributes its value on output

**Source:** 8.9 p2 second clause, physical PDF146. **Class:** Effect.

**Definition:** When a variable occurs multiple times in one group's object list, its value appears on
output once for each occurrence. The list is not a set of unique variables. Repetition
in declaration lists is distinct from repeated assignments in namelist input and from
permitted compression of successive identical values within one group object's output.

**Diagnostic obligation:** not-required.

**Facets:** `separated-repeated-scalar`, `adjacent-repeated-scalar`, `repeated-array-occurrence-source`, `compression-and-input-boundary`.

**Oracle:** Actual output occurrence/value sequences and counters against literal expectations, with
deliberate dropped/reordered duplicate countermodels.

**Oracle limitation:** No cases or parser are implemented. A same final value after READ, successful
serialization or unique-name dictionary does not prove multiplicity. Keep canonical
formatting and input rules separate.

**Dependencies:** 8.9p2/p3;13.11.3.1p2;13.11.3.2p1/p2;13.11.4.1;13.11.4.3p1-p4;12.6.3;19.6.2.

### S8.9-003: Repeated local group declarations append their object lists

**Source:** 8.9 p3, physical PDF146. **Class:** Effect.

**Definition:** Each successive appearance of a group name in NAMELIST statements of one scoping unit
continues that group's object list. Repeating the group is permitted, and neither the
last declaration alone nor a set-union of unique members replaces the concatenated list.
Different scoping units can identify different groups despite a shared spelling.

**Diagnostic obligation:** not-required.

**Facets:** `same-statement-continuation`, `successive-statement-continuation`, `interleaved-group-lists`, `scope-and-occurrence-source`.

**Oracle:** Exact declaration-order list concatenation with actual nonempty output/value
observations and separately checked group identity.

**Oracle limitation:** No fixture or graph is supplied. C815's attribute-uniqueness rule is not used to ban
this expressly permitted repeated group. Compile-only acceptance does not establish
appended runtime output.

**Dependencies:** R871;C8107;8.9p2/p4;3.120;19.3.1;19.5.1.4p2(15);13.11.4;12.6.2.1C1216/C1217.

### S8.9-004: Group objects have their type, kind parameters and rank established through a permitted route

**Source:** 8.9 p5 first sentence, physical PDF146. **Class:** Restriction.

**Definition:** A group object is accessed by use or host association, or its declared type, kind type
parameters and rank are established by prior statements in the same scoping unit or by
the applicable implicit typing rules. These are alternative routes, not a universal
requirement for a new explicit local declaration. The first sentence specifically names
kind parameters and rank; later implicit-type confirmation has its own condition.

**Diagnostic obligation:** context-dependent.

**Facets:** `prior-explicit-properties`, `use-associated-properties`, `host-associated-properties`, `late-rank-source-contrast`, `implicit-scalar-control`, `kind-length-and-state-boundaries`.

**Oracle:** Complete finite declaration/association/implicit-mapping graphs and precisely qualified
ordering controls.

**Oracle limitation:** The prose does not itself require fatal rejection or prescribe a message. Unknown types,
invalid implicit contexts or unsupported kind probes are not a different ordering
predicate; metadata/source evidence remains pending.

**Dependencies:** 8.2;8.7p1/p3/p4;8.5.8;10.1.11;14.2.2p2/note4;19.5.1.4p1/p2;8.8;C8107-C8109;4.2p2.

### S8.9-005: Later declarations of implicitly typed group objects confirm the implied type and parameters

**Source:** 8.9 p5 second sentence, physical PDF146. **Class:** Restriction.

**Definition:** If a group object was typed by implicit typing rules, a subsequent type declaration
confirms that implied type and its parameters. The condition is not applied
indiscriminately to a prior explicitly typed or associated object, and changing a
letter's assumed default without reading the actual implicit mapping is not a valid
oracle.

**Diagnostic obligation:** context-dependent.

**Facets:** `later-matching-type-control`, `later-different-type-source`, `length-kind-mapping-source`, `prior-explicit-and-associated-boundary`.

**Oracle:** Actual implicit-map and statement-order source contrasts with conforming one-change
repairs and explicit scope/type-parameter prerequisites.

**Oracle limitation:** No compiler observation or policy is supplied. A NULL implicit mapping, unsupported kind
or already-explicit duplicate declaration cannot stand in for the conditional
later-confirmation requirement.

**Dependencies:** 8.7R866-R869/p1/p3/p4;8.2;7.4.4.2;8.9p5;14.2.2;19.5.1.4;4.2p2.

<!-- END GENERATED 8.9 -->
