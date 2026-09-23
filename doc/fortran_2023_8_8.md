# Fortran 2023 8.8: IMPORT statement

The canonical record is `doc/catalogues/import_statement_8_8.json`.
Effective status is `Registry.catalogue_review_state("8.8")`. This draft
accounts for source and proposes finite evidence; it supplies no fixture,
compiler observation, profile, review, canonical link or SourceUses instance.
Every new facet remains pending.

The authority is J3/24-007, December 18, 2023, 688 physical pages,
SHA-256 `7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The complete section spans physical PDF143-145, from the IMPORT heading
through all five notes, ending at the actual8.9 NAMELIST heading.
It contains R870, C8100-C8106, five prose paragraphs and five notes.
The eight numbered units were already globally accounted; the five prose
paragraphs and five notes are the ten newly accounted base units.

R870 has four alternatives. Bare IMPORT differs from a nonempty basic list,
which can have `::`; ONLY requires a list after its comma and single colon,
while NONE and ALL take no list. `IMPORT ::` is not another bare form.
The complete502-head original grammar scan finds no explicit `import-name`
production, so R402 supplies the name convention and R401 the nonempty list.
There is no rename, selected subobject or generic-operator form.

## Scope, identity and ordering

IMPORT follows USE and precedes IMPLICIT/declarations under R504. It is
not a late declaration or an executable instruction. Its placement inside
an otherwise permitted scoping-unit category must still have a grammar slot.
R726 supplies no IMPORT statement inside a derived-type definition, even
though that definition has default host access.

C8100's main/external/module/BLOCK DATA exclusions apply to their own
scoping units, not every nested interface, procedure or BLOCK in the file.
A genuine submodule must satisfy C1412: its ancestor declares a separate
module procedure. An empty ancestor with no such declaration is not a
positive control. IMPORT,NONE is excluded from the submodule's own scope,
not automatically every separately nested procedure.

Every listed name resolves to an actual host entity under C8101. A host's
USE rename supplies its actual local name; IMPORT does not add renaming.
C8105 permits prior explicit host declarations or the stated host/use
association alternatives for interface-body access. Importing a later
local host type is not automatically valid, and a missing-type recovery
message does not prove a uniquely isolated C8105 violation.

C8106 prevents the19.5.1.4 hiding contexts for explicitly listed names and
ALL-accessible entities. Bare/default access retains normal hiding instead.
One keyword or same-spelled declaration cannot establish entity identity.
Existing canonical type/name/interface cases keep their actual owners and
roles; no numbered-wrapper reuse or source graph is created by this draft.

## Prose requirements and defaults

Seven append-only S requirements separate the paragraph meanings:

| Requirement | Scoped meaning |
| --- | --- |
| S8.8-001 | ONLY restricts host association outside BLOCK to the union of lists |
| S8.8-002 | BLOCK ONLY filters enclosing local/construct identifiers |
| S8.8-003 | NONE blocks host association; ordinary interface bodies default to it |
| S8.8-004 | BLOCK NONE makes enclosing local/construct identifiers inaccessible |
| S8.8-005 | ALL gives host access with C8106's no-hiding condition |
| S8.8-006 | Bare/default host access retains ordinary hiding exceptions |
| S8.8-007 | Listed imports make named entities accessible outside BLOCK |

These are static scope meanings, not execution of IMPORT. Planned value
observers must operate on the actual resolved entities, with independent
literal values and counted complete calls; declaration-only empty runs are
not effects. Other facets require finite source/interface/use evidence with
an explicit denominator. No such mechanism is implemented here.

Ordinary and abstract interface bodies do not have the same default as a
MODULE-prefixed procedure interface body. A generic interface containing
MODULE PROCEDURE names is not that body kind. IMPORT,NONE and ONLY do not
mean IMPLICIT NONE or reset an inherited implicit mapping. A legitimate
local or USE-associated entity is a separate route, not host access through
a forbidden name.

BLOCK is especially distinct. An implicitly declared object used only
inside BLOCK can belong to the enclosing inclusive scope, not a new BLOCK
entity. Note4's intentionally invalid program and ONLY:X repair retain that
premise. A truly explicit BLOCK-local declaration is a different control.
IMPORT itself is excluded from the specifications creating construct
entities under11.1.4p2/19.4p3. Do not insert IMPLICIT statements into BLOCK
or treat all global/intrinsic identifiers as the p1/p2 local/construct set.

## Notes and evidence boundaries

The five notes are informative. Note1 omits the surrounding eligible host
and shows abbreviated ordering; any completed fixture must obey R504, not
infer an ordering exception. Notes2/3 do not define every value read in their
snippets, so they cannot be copied as runtime oracles without that context.
Note5's opaque type and dummy-procedure interface need complete declarations
and implementations for a call; IMPORT grants type-name access, not PRIVATE
component access or an opaque representation oracle.

Numbered violations require reporting capability, not fatal rejection,
particular English or printed identifiers. Prose restrictions keep an actual
numbered/name-scope or explicit policy basis before negative fixtures.
Unsupported features, missing providers, undefined data, source echoes,
compiler failures and no-op execution are not substitutes for that evidence.

<!-- BEGIN IMPORT STATEMENT FIXTURES -->
## IMPORT statement executable packet

Fifteen fixtures cover twenty selected facets of 8.8. Runtime fixtures observe ONLY, NONE, ALL, bare, and listed IMPORT effects through nonzero integer values and host-object state, and the R870 form fixture executes every admitted selected form in eligible internal scopes. The interface-body fixture imports a host derived type, kind parameter and shape constant into an ordinary interface body, then calls the declared procedure and checks the returned 42_rk value.

C8100 diagnostics place bare IMPORT in the scoping unit of a main program, external subroutine, module, and block data. Each repair deletes exactly that IMPORT and runs a complete control. Frozen LFortran currently accepts the external-subprogram negative; the case is retained because gfortran diagnoses it and C8100 requires it.

Feature mutations are permanent generator data. The ONLY/NONE/ALL/bare mutations compensate local declarations so the mutants remain conforming and fail at run time by changing whether hz is the host object or a local object. The interface fixture has a conforming alternate-shape-constant mutation that compiles and fails at run time; C8101-C8106, BLOCK, submodule, ordinary-interface defaults, shadowing negatives, empty-list syntax, and source-graph inventory not listed in this summary remain pending.
<!-- END IMPORT STATEMENT FIXTURES -->

<!-- BEGIN GENERATED 8.8 -->

### R870: IMPORT has a basic optional-list form and distinct ONLY, NONE and ALL forms

**Source:** 8.8 R870, J3/24-007, 18 December 2023, physical PDF143. **Class:** Syntax.

**Definition:** IMPORT may stand alone or have a nonempty import-name list optionally preceded by ::.
The other alternatives are IMPORT, ONLY: followed by a required list, IMPORT, NONE, and
IMPORT, ALL. The basic optional separator is inside the optional list group; IMPORT::
alone is not the listless form. R401 and assumed R402/R603 govern lists and names. No
rename, selector, generic-spec or declaration suffix is part of import-name.

**Diagnostic obligation:** required.

**Facets:** `bare-form`, `basic-list-no-colon`, `basic-list-double-colon`, `basic-multiple-names`, `only-required-list`, `none-form`, `all-form`, `empty-list-and-separator-exclusions`, `modifier-punctuation`, `name-not-designator-or-rename`, `scope-and-order-source`.

**Oracle:** Complete legal host/scoping contexts and source-minimal grammar repairs, with exact list
and modifier alternatives independently derived from the original production. Compile
admissions, semantic scope effects and diagnostic causes remain separate.

R870 executable syntax-form fixtures: one complete run/positive-control/f2023 program
contains a bare IMPORT, a basic IMPORT name with no double colon, a basic IMPORT :: list
containing two names, two IMPORT, ONLY: statements with required nonempty lists, one
IMPORT, NONE, and one IMPORT, ALL in distinct eligible internal scoping units. Each
subprogram returns a checked nonzero value or host-state effect before the program emits
its completion line, so the syntax admissions are not empty compile-only parses.

**Oracle limitation:** Required numbered reporting is not mandatory fatal status, fixed English or printed
R870. Wrong host role, ordering, C8102/C8104 combinations, C8106 hiding, missing
providers, unsupported syntax, source echoes and native failures are not a different
grammar predicate. No fixture or scope-use graph is supplied.

R870 executable syntax-form boundaries: only the seven selected positive form facets are
covered. Empty lists, malformed punctuation, designators, renames, generic syntax,
source-order mapping, and numbered syntax diagnostics remain pending.

**Dependencies:** 4.1.3R401/R402/p2;6.2.2R603/C601;5.1R504;5.3.2;7.5.2.1R726;11.1.4R1109;C8100-C8106;19.5.1.4;4.2p2.

### C8100: IMPORT is excluded from four top-level scoping-unit categories

**Source:** 8.8 C8100, physical PDF143. **Class:** Restriction.

**Definition:** An IMPORT statement does not appear in the scoping unit of a main program, external
subprogram, module or block data program unit. The restriction names the actual scoping
unit, excluding nested scopes; it is not a ban everywhere in a file or module. Other
syntax and constraints still govern allowed nested and submodule contexts.

**Diagnostic obligation:** required.

**Facets:** `main-program-exclusion`, `external-subprogram-exclusion`, `module-exclusion`, `block-data-exclusion`, `nested-scope-controls`, `grammar-admission-not-sufficient-source`.

**Oracle:** Complete scope-category controls and one-statement deletion repairs with no name-list,
provider or ordering defect. Preserve exact inclusive/nested scoping distinctions.

C8100 top-level exclusion diagnostic fixtures: four compile/diagnose negatives place a
bare IMPORT as the only selected defect in the scoping unit of a main program, external
subroutine, module, or block data program unit. The paired controls delete exactly that
IMPORT statement and otherwise keep the same complete source; each control links and
runs, observing a nonzero value. The diagnostic must be located on the IMPORT line and
must not be an unsupported-feature, internal-compiler, source-echo, or crash report. The
external-subprogram case exposes a frozen LFortran acceptance defect; gfortran diagnoses
it under the pinned text.

**Oracle limitation:** A report claiming IMPORT is universally interface-body-only is not adopted as the
language definition. The finite malformed scopes and conforming nested controls need
independent cause/mode evidence; unsupported permitted contexts cannot be recast as this
constraint.

C8100 top-level exclusion diagnostic boundaries: only bare IMPORT exclusions in four
top-level scoping-unit categories are covered. Nested eligible scopes, submodule
contexts, derived-type grammar, and other constraints remain pending. Block data and
COMMON are used only to make the deletion control run.

**Dependencies:** 3.120;5.1R502-R504;5.2.1;5.3.2;7.5.2.1R726;11.1.4R1109;14.2.3C1412;15.4.3.2R1505;19.1;4.2p2.

### C8101: Each import-name denotes an entity in the host scoping unit

**Source:** 8.8 C8101, physical PDF144. **Class:** Restriction.

**Definition:** Every listed import-name is the name of an entity in the host scoping unit. A name in
some other module, a missing entity, or only a new declaration inside the importing
scope does not by itself meet this condition. The host's actual accessible name and the
imported entity's identity matter; IMPORT does not rename or create that host entity.

**Diagnostic obligation:** required.

**Facets:** `missing-host-name`, `host-declared-entity-kinds`, `host-use-renamed-name`, `actual-host-identity-source`.

**Oracle:** Actual host entity/name bindings and otherwise complete one-name repairs, without
conflating absence, type compatibility, visibility or prior-declaration conditions.

**Oracle limitation:** No arbitrary missing type or provider error counts automatically as C8101. Named
constants, variables, types and procedure/interface names are not interchangeable merely
because they share a spelling. All source graph and compiler evidence remains pending.

**Dependencies:** R870;4.1.3R402;6.2.2;C8105/C8106;14.2.2p2/p7;19.1;19.3.1;19.5.1.4;8.7;4.2p2.

### C8102: An ONLY import requires every IMPORT in that scope to use ONLY

**Source:** 8.8 C8102, physical PDF144. **Class:** Restriction.

**Definition:** If any IMPORT in a scoping unit has ONLY, every IMPORT in that same scoping unit has
ONLY. This is independent of source order and is not a last-statement-wins choice.
Multiple ONLY lists are permitted subject to all other rules; their accessibility
meaning is the p1 union, not a replacement list.

**Diagnostic obligation:** required.

**Facets:** `only-and-basic-list`, `only-and-bare-import`, `none-all-overlap-source`, `multiple-only-controls`, `separate-scope-boundary`.

**Oracle:** Same-scope mode matrices and exact minimal corrections with no cardinality, host-name or
shadowing confounds.

**Oracle limitation:** No file-wide token count, presumed sequential overriding, duplicated C8104 credit or
fatal-status requirement. Every actual report still needs its live source, valid control
and qualified mode.

**Dependencies:** 3.120;R870;C8101/C8104/C8106;8.8p1;19.1;4.2p2.

### C8103: IMPORT, NONE is excluded from a submodule's own scoping unit

**Source:** 8.8 C8103, physical PDF144. **Class:** Restriction.

**Definition:** IMPORT, NONE does not appear in the scoping unit of a submodule. This is not a ban on
every IMPORT form or on statements in separately nested procedure scopes. The submodule
and its declared ancestor relationship must be legitimate before evaluating the
exclusion.

**Diagnostic obligation:** required.

**Facets:** `submodule-none-exclusion`, `submodule-default-control`, `contained-procedure-and-ancestor-source`.

**Oracle:** A complete buildable ancestor/submodule pair with one deleted statement, not a missing
module file or incompatible separate-procedure definition.

**Oracle limitation:** No processor-support or module-artifact failure is a successful C8103 report. The rule
supplies neither a universal module-scope prohibition nor a runtime host-lifetime
effect.

**Dependencies:** C8100/C8104-C8106;3.120;14.2.3R1416-R1419/C1412;15.4.3.2p4;15.6.2.5R1541-R1543/C1577/C1578;19.5.1.4;4.2p2.

### C8104: NONE or ALL permits no other IMPORT in its scoping unit

**Source:** 8.8 C8104, physical PDF144. **Class:** Restriction.

**Definition:** If a scoping unit contains IMPORT, NONE or IMPORT, ALL, it contains no other IMPORT
statement. Repeating the same form still supplies another statement; the rule does not
mean only that the two keywords cannot be mixed. Separate scopes and basic/ONLY-only
collections keep their own conditions.

**Diagnostic obligation:** required.

**Facets:** `repeated-none`, `repeated-all`, `mixed-none-all`, `other-form-companions`, `same-scope-and-single-controls`.

**Oracle:** Complete same-scope statement cardinalities and exact one-deletion controls, preserving
actual mode antecedents and scope boundaries.

C8104 single NONE/ALL positive-control fixture: one complete run/positive-control/f2023
source contains a single IMPORT, NONE in one internal subroutine and a single IMPORT,
ALL in a different internal subroutine. No scoping unit contains a second IMPORT
statement alongside either form. Both scopes are called and checked with nonzero values,
so the control proves the single-statement premise without relying on a no-op compile
admission.

**Oracle limitation:** No token count across a file, implicit default treated as an extra statement,
unsupported-mode report or unqualified English/fatal-exit predicate.

C8104 single NONE/ALL positive-control boundaries: only the positive single-statement
side of C8104 is covered. Repeated NONE, repeated ALL, mixed NONE/ALL, companions with
other IMPORT forms, and same-scope diagnostics remain pending.

**Dependencies:** 3.120;R870;C8100-C8103/C8106;8.8p2-p4;19.1;4.2p2.

### C8105: Host entities used in an interface body satisfy association or prior-declaration conditions

**Source:** 8.8 C8105, physical PDF144. **Class:** Restriction.

**Definition:** An entity accessed by host association within an interface body is accessible by host or
use association within that body's host scoping unit, or is explicitly declared before
the interface body. The alternatives are not a blanket requirement for a new local
declaration immediately before every IMPORT, nor permission to import an otherwise
unavailable later host entity.

**Diagnostic obligation:** required.

**Facets:** `prior-local-type-control`, `forward-local-type-source`, `host-associated-route`, `use-associated-route`, `interface-kind-and-cause-source`.

**Oracle:** Complete declaration/association graphs and one-order-change source contrasts, with
actual interface kind and imported entity identity. No unique cause is assumed before
qualifying the whole context.

**Oracle limitation:** Host/use association is an explicit alternative to a prior immediate-host declaration.
Compiler forward-resolution behavior, missing type/module errors or agreement cannot
replace the original condition.

**Dependencies:** C8101/C8106;5.1R504;7.3.2.1;7.5.2.1/.2;14.2.2;15.4.3.2p2-p7;19.5.1.4p1/p2;4.2p2.

### C8106: Explicitly imported or ALL-accessible names are not hidden by local contexts

**Source:** 8.8 C8106, physical PDF144. **Class:** Restriction.

**Definition:** An entity named in an IMPORT list, or made accessible by IMPORT, ALL, is not placed in a
context from19.5.1.4 that would hide the host entity of that name. The imported-name and
ALL antecedents matter. Bare IMPORT/default host access instead retains p4's ordinary
hiding exception; identifiers and entity roles are not interchangeable.

**Diagnostic obligation:** required.

**Facets:** `basic-listed-name-shadow`, `only-listed-name-shadow`, `all-name-shadow`, `dummy-result-and-use-contexts`, `complete-local-identifier-source`, `bare-unlisted-shadow-controls`.

**Oracle:** Actual imported entity bindings and precisely identified hiding contexts with complete
minimal controls. Full source/name graphs, not declaration keywords, determine the
predicate.

**Oracle limitation:** Do not universalize ALL's no-hiding condition to bare IMPORT/default scope, or interpret
a genuine different-entity declaration as mutation of the host object. Reporting needs a
live source and valid context; no new runtime or canonical-link evidence is supplied.

**Dependencies:** 8.8p1/p3-p5;C8101/C8105;19.3.1;19.5.1.4p1/p2/p3;8.7;14.2.2;11.1.4p2;4.2p2.

### S8.8-001: ONLY restricts non-BLOCK host association to names listed in that scope

**Source:** 8.8 p1 first sentence, physical PDF144. **Class:** Restriction.

**Definition:** Outside BLOCK, if IMPORT with ONLY appears, host association requires the entity's name
to occur in an IMPORT list in that scoping unit. Names from multiple conforming ONLY
lists are considered together. This restricts host association, not separately valid
local declarations, USE association or intrinsic type availability.

**Diagnostic obligation:** context-dependent.

**Facets:** `listed-name-union`, `unlisted-host-name-exclusion`, `independent-use-and-local-routes`, `nested-host-paths`, `intrinsic-and-mapping-boundaries`.

**Oracle:** Finite source/use/interface graphs with named host identities, nonhost-route controls
and individually justified observables where a real effect program is appropriate.

S8.8-001 ONLY host-access runtime fixture: one internal subroutine has two IMPORT, ONLY:
statements that import host integers hx and hy. A same-spelled host hz is deliberately
not in either list; the subroutine declares its own local hz, assigns it the nonzero
value 7, and returns hx+hy+hz = 18. The host hz starts at 100 and is checked unchanged
after the call. A conforming feature mutation adds hz to an ONLY list and removes the
compensating local declaration, which keeps the program valid but changes the host hz to
7 and fails the host-state check.

**Oracle limitation:** No implemented graph or fixture is supplied. A declaration-only empty run, type keyword
acceptance or aggregate count cannot prove the complete host-access restriction. Exact
reporting ownership and named-constant/bound prerequisites remain required.

S8.8-001 ONLY host-access runtime boundaries: only a non-BLOCK internal subprogram with
two ONLY lists, imported integer objects, and one explicit local same-spelled object is
covered. BLOCK-only rules, USE routes, intrinsic names, and nested host graphs remain
pending.

**Dependencies:** C8101/C8102/C8105/C8106;8.8p5;8.7;7.1.2;5.1R504;14.2.2;19.1p2;19.5.1.4;4.2p2.

### S8.8-002: BLOCK ONLY lists make unlisted enclosing local and construct identifiers inaccessible

**Source:** 8.8 p1 second sentence, physical PDF144. **Class:** Restriction.

**Definition:** When BLOCK contains ONLY imports, identifiers of local and construct entities in its
host scoping unit are inaccessible there unless they appear in at least one of its
import-name lists. This is the union of all lists and uses BLOCK's
identifier/inclusive-scope rules, not a blanket internal-procedure host-association
model.

**Diagnostic obligation:** context-dependent.

**Facets:** `block-list-union`, `implicit-enclosing-entity-boundary`, `separate-local-construct-control`, `nested-construct-identity-source`.

**Oracle:** Source-bound finite BLOCK identifier inventories and role-valid controls, with
separately justified scope-diagnostic or real-value evidence.

**Oracle limitation:** No hidden host-association substitute, implicit-new-local assumption, undefined payload
inquiry or no-op runtime classifier. IMPLICIT statements are not inserted into R1109's
BLOCK specification grammar.

**Dependencies:** 8.8note4;C8101/C8102/C8106;11.1.4R1109/p2;19.1p2;19.4p3;5.4.3.2.2;8.7p3/p4/note3;4.2p2.

### S8.8-003: NONE disables host association and is the ordinary interface-body default

**Source:** 8.8 p2 first and second sentences, physical PDF144. **Class:** Restriction.

**Definition:** IMPORT, NONE makes host entities unavailable by host association in its scoping unit. An
interface body other than a module procedure interface body has this behavior by
default. This neither prohibits independent USE/local entities nor gives all interface
bodies the same host default. BLOCK has the separately specified identifier rule.

**Diagnostic obligation:** context-dependent.

**Facets:** `explicit-none-host-exclusion`, `ordinary-interface-default`, `independent-use-and-local-control`, `implicit-mapping-is-separate`, `module-interface-default-boundary`.

**Oracle:** Exact interface/scope kinds and independent name-path controls, with missing-host
semantics separated from implicit typing and actual procedure implementation.

S8.8-003 NONE host-access runtime fixture: one internal subroutine begins with IMPORT,
NONE, declares its own local hz, assigns that local value 7, and returns it while the
host hz remains the nonzero sentinel 100. The feature mutation replaces NONE by ALL and
removes the local declaration, so the same assignment reaches the host object and the
caller's unchanged-host check fails.

**Oracle limitation:** No universal interface-body rule, external/link failure, copying mechanism or compulsory
runtime trap. The ordinary-interface default is a semantic rule even without an IMPORT
token; it needs a finite qualified witness, not a keyword census.

S8.8-003 NONE host-access runtime boundaries: only explicit IMPORT, NONE in an internal
subprogram and a separate explicitly declared local integer are covered.
Ordinary-interface default NONE, module-procedure interface boundaries, implicit typing,
and independent USE routes remain pending.

**Dependencies:** C8100/C8103-C8106;8.8p4;8.7p3/p4;15.4.3.2p2/p4/p5;19.5.1.4p1/note2;7.1.2;14.2.2;4.2p2.

### S8.8-004: BLOCK NONE makes enclosing local and construct identifiers inaccessible

**Source:** 8.8 p2 final sentence, physical PDF144. **Class:** Restriction.

**Definition:** IMPORT, NONE in BLOCK makes identifiers of local and construct entities in the host
scoping unit inaccessible in that BLOCK. It does not create new local variables for
otherwise implicitly declared names, nor prohibit a genuinely separate explicitly
declared BLOCK entity. Identifier categories and inclusive scope remain operative.

**Diagnostic obligation:** context-dependent.

**Facets:** `implicit-outer-name-exclusion`, `explicit-block-local-control`, `enclosing-construct-entity-source`, `identifier-category-boundary`.

**Oracle:** Finite inclusive-scope/construct-entity graphs and complete note-derived contrasts, not
a fabricated host-value runtime classification.

**Oracle limitation:** No undefined read or IMPLICIT statement in BLOCK, no blanket ban on new explicit locals,
and no automatic mandatory diagnosis from prose alone. Actual numbered/name-scope or
policy bases precede negative metadata.

**Dependencies:** 8.8note4;11.1.4R1109/p2;19.1p2;19.3.1;19.4p3;8.7p3/p4/note3;5.4.3.2.2;4.2p2.

### S8.8-005: ALL makes every host entity accessible subject to the no-hiding constraints

**Source:** 8.8 p3, physical PDF144. **Class:** Effect.

**Definition:** IMPORT, ALL makes all entities from the host scoping unit accessible in the importing
scoping unit. Actual host identity and C8104-C8106 still apply. It is stronger than
ordinary default host access with respect to hiding, not a new copy of every host object
or an extension of the host instance's lifetime.

**Diagnostic obligation:** not-required.

**Facets:** `actual-host-value-observation`, `host-type-and-interface-source`, `no-hiding-relation`, `finite-all-scope-inventory`.

**Oracle:** Actual host-entity observations where executable, and finite source/interface mappings
otherwise, with independently established identities and values.

S8.8-005 ALL host-access runtime fixture: one internal subroutine begins with IMPORT,
ALL and uses two host integers: hx remains 5, hz is updated from 100 to 7, and the
returned sum hx+hz is 12. The feature mutation narrows the import to ONLY: hx and
inserts a compensating local hz declaration, so the program remains conforming while the
required host update disappears.

**Oracle limitation:** No fixtures are implemented. One scalar update cannot prove every host entity/category
or scope. ALL does not promise physical copying, access to an unrelated module or use of
an ended host instance.

S8.8-005 ALL host-access runtime boundaries: only two ordinary host integer variables in
an internal subprogram are covered. Other host entity classes, BLOCK scopes, and C8106
no-hiding negatives remain pending.

**Dependencies:** C8100/C8103-C8106;8.8p4;19.5.1.4;19.1;7.5.2.1R726;14.2.3;15.4.3.2;19.6.2;4.2.

### S8.8-006: Bare IMPORT and designated default scopes provide host access with normal hiding exceptions

**Source:** 8.8 p4, physical PDF144. **Class:** Effect.

**Definition:** Bare IMPORT, with neither a specifier nor a name list, gives access to host entities
except where19.5.1.4 makes a host name inaccessible. This is the default for a
derived-type definition, internal subprogram, module procedure interface body, module
subprogram or submodule. The list of default scopes does not insert IMPORT into
otherwise ineligible grammar; bare/default behavior is not ALL's no-hiding rule.

**Diagnostic obligation:** not-required.

**Facets:** `bare-host-value-observation`, `default-internal-module-scopes`, `legitimate-local-shadow`, `module-interface-default`, `derived-type-default-source`, `submodule-default-source`, `all-versus-bare-source`.

**Oracle:** Real name-resolution/value observations and independently bound
source/interface/declaration graphs, preserving defaults and ordinary shadowing
exceptions.

S8.8-006 bare IMPORT host-access runtime fixture: one internal subroutine uses bare
IMPORT to access host hx and hz, assigns hz = 6, returns hx+hz = 11, and the caller
observes the host hz changed to 6. The feature mutation narrows access to ONLY: hx and
inserts a local hz declaration, keeping the mutant conforming while making the
host-state oracle fail.

**Oracle limitation:** No cases are implemented. IMPORT is not executable copying, no-op output is not host
access, and a finite scalar witness is not universal coverage of every default scope or
name class.

S8.8-006 bare IMPORT host-access runtime boundaries: only explicit bare IMPORT in an
internal subprogram is covered. Default host access in scopes with no IMPORT, legitimate
local-shadow controls, derived-type definitions, module procedure interface bodies,
module subprograms, and submodules remain pending.

**Dependencies:** 8.8p2/p3/p5;C8105/C8106;19.5.1.4p1/p2;7.5.2.1R726;7.3.2.1C704;10.1.11;14.2.3C1412;15.4.3.2p4;8.7;19.1;19.3.1.

### S8.8-007: Listed IMPORT makes each named host entity accessible outside BLOCK

**Source:** 8.8 p5, physical PDF144. **Class:** Effect.

**Definition:** Outside BLOCK, an IMPORT with an import-name list makes each named host entity
accessible. This positive availability rule is not itself the ONLY exclusion rule and
does not erase C8101, C8105 or C8106. Ordinary interface bodies, other host defaults and
BLOCK-specific identifier rules retain their distinct conditions.

**Diagnostic obligation:** not-required.

**Facets:** `ordinary-interface-type-availability`, `multiple-basic-lists`, `host-local-name-identity`, `basic-versus-only-source`, `block-and-opaque-type-boundaries`.

**Oracle:** Exact listed-name/source/interface connections and actual finite observations where
legitimate, without changing existing canonical type/interface cases or roles.

S8.8-007 interface-body listed IMPORT fixture: one module procedure contains an ordinary
interface body for external subroutine monitor. IMPORT :: box, rk, slot_count makes the
prior host derived type, kind parameter and named constant available for the dummy
declarations. A call through that explicit interface passes two box values, 31_rk and
11_rk; the external procedure sums the explicit-shape dummy and returns 42_rk, which the
main program checks at run time.

**Oracle limitation:** No fixture, linked evidence or graph is implemented. A bare name token, unknown-type
error, opaque representation probe or empty run cannot establish the required entity
correspondence.

S8.8-007 interface-body listed IMPORT boundaries: only a prior module type, kind
parameter and integer named constant imported into one ordinary interface body are
covered. Multiple basic lists, USE-renamed host names, BLOCK behavior, opaque PRIVATE
representation, and full source graph inventory remain pending.

**Dependencies:** C8101/C8105/C8106;8.8p1/p2/p4/note5;7.5.2.2;7.1.2;14.2.2;15.4.2.2;15.4.3.2;19.5.1.4;19.1;11.1.4.

<!-- END GENERATED 8.8 -->
