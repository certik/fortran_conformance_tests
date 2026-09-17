# Fortran 2023 8.3: Automatic data objects

**INDEPENDENTLY SOURCE-REVIEWED; ALL FIXTURES PENDING.** No fixtures,
executable models, compiler observations or fixture approvals are added.
Source/inventory adjudication is recorded in `doc/source_audits/batch_027.json`.
The catalogue is
`doc/catalogues/automatic_data_objects_8_3.json`; all finite facet plans and
definition/source-use plans are explicitly pending.

Source: J3/24-007, December 18, 2023, 688 pages, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The original physical PDF119, printed105, is bounded by the actual 8.3 and
8.4 headings. All three original unit hashes and the section hash
`e3e7219b831bb7157c2ccfdcaa30503c4c0de279d816849b5c80e7e6e19aa187`
were reproduced with the checksum-pinned typography helpers.

| Original unit | PDF119 lines | Treatment |
| --- | --- | --- |
| `p1` | 2-3 | Six definition predicates; no invented automatic-object classifier execution |
| `C814` | 4 | Canonical SAVE exclusion and qualified report/control plans |
| `p2` | 5-9 | Entry establishment and invariance of nonconstant local type parameters |

The map contains three base units, nineteen fine units and twenty-two
accounting rows. Its two requirements have eighteen facets, all pending.
The committed baseline has no C814 or local 8.3/8.4 primary cases; none are
silently mapped, copied or re-owned.

Automatic is not a synonym for a stack allocation or every dynamically
sized value. A dummy is excluded from the definition, but is not therefore
an eligible saved control. A formal constant inquiry can mention a variable
without reading its payload. Nondeferred variable lengths on scalar
POINTER/ALLOCATABLE entities are not globally excluded from the automatic
predicate; colon/asterisk parameter routes remain different.

BLOCK specification expressions have processor-dependent evaluation order.
The proposed snapshots mutate their source variables only after entry;
they do not count specification-function calls or assume left-to-right
evaluation. A no-list SAVE admission is confined to a procedure, since
C1108 requires a saved-entity list inside BLOCK. An outer SAVE does not
extend to local BLOCK construct entities.

The recent RANK qualification is retained: 16.9.171p3 requires a **data
object**. A constructor/other expression value is not automatically one.
No direct `RANK([...])` is planned, and a fixed-rank destination is not a
constructor-rank oracle. If a separate constructor witness is needed,
its observer must be an actual assumed-rank dummy data object with valid
argument association. This packet does not alter the array-constructor
source plans or the separate implementation undergoing correction.

Source-use/evidence infrastructure remains unapproved and unimplemented
for these plans. No graph credit, profile fallback, mandatory prose
diagnostic, undefined-value trap or compile-only replacement for an effect
is introduced. The definitions below are generated with
`Registry.render(write=True)` for this owned view only.

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

**Oracle limitation:** All facets are pending, with no fixtures or reports. A valid control is not made by
turning the object into a dummy or function result, which C862 separately excludes from
explicit SAVE. C808/C880 initializer prohibitions and main/module
nonconstant-specification restrictions must not be used as substitute causes. Reject
bare SAVE/constant words, source echoes, unrelated declarations, unsupported facilities,
Internal/ASR/crash/resource failures and generic recovery. No unsaved-value trap, forced
memory clearing, stack layout or byte-width oracle.

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
