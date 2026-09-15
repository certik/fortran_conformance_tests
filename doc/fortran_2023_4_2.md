# Fortran 2023: 4.2 Conformance

Draft catalogue: `doc/catalogues/processor_conformance.json`. Source:
pinned J3/24-007, dated 18 December 2023, PDF 46-47, printed 32-33.
The census includes all eight paragraphs, the continuation of p5 on PDF 47,
all ten p2 obligations, and 55 fine subdivisions.

Thirteen S requirements preserve actual universal or conditional
obligations. All 24 registry facets are explicitly pending. There are
**no 4.2 executable cases**: a hello-world, an accepted extension, or one
rejected source cannot certify universal execution or reporting capability.
The canonical JSON supplies the exact proposed evidence contract for
every pending facet.

| Source | IDs | Required evidence boundary |
| --- | --- | --- |
| p2(1) | S4.2-001 | Reviewed whole-suite source/effect aggregation with justified limits and external premises |
| p2(2) | S4.2-002 | Obsolescent census, numbered detectability, reporting modes, and conforming-report evidence |
| p2(3)-(6) | S4.2-003 through S4.2-006 | Syntax/constraint, deleted-form, kind-support, source-interface, and whole-program scope evidence |
| p2(7)-(9) | S4.2-007 through S4.2-009 | Qualified intrinsic/module extension inventories and actual resolution/reporting evidence |
| p2(10) | S4.2-010 | Processor rejection-category and reason-reporting evidence |
| p4 | S4.2-011 and S4.2-012 | Extension compatibility, EXTERNAL protection, and resolved program-use review |
| p6 | S4.2-013 | Applicable processor-dependent facility census and qualified methods/semantics |

Reporting is a processor **capability**, not necessarily rejection and not
necessarily active on every invocation. The p3 exemption is determined by
whether the format specification is part of a FORMAT statement, not by
whether its text is known at compile time. The exemption permits missing
reports for the specified categories; it does not require silence or make
an invalid character format standard conforming. An obsolescent conforming
program must not be mislabeled invalid just to use `outcome: diagnose`.

Size and complexity limits, nonportable standard items, non-Fortran
dependencies, compatible extensions, intrinsic-name conflicts, and
processor-dependent methods all remain qualified in the definitions.
Processor dependence does not permit omission of a required facility.
No profile skip, context-only assertion, or invented source attribution
stands in for documentary or aggregate evidence.

Paragraphs 7-8 use **should**, not **shall**. They recommend processor
documentation; they are not informative notes or mandatory S obligations.
The `recommendation` source-accounting disposition classifies both base
units and their six documentary subunits without creating mandatory
requirements, cases or implementation passes. Actual adherence to the
advice remains unexamined: a documentary assessment would need qualified
evidence for limit values/reporting, extensions and their reporting,
deleted/obsolescent reporting, and processor-dependent semantics. The
definitional final sentence of p7 stays separate. Closing this classification
gap does not close the 24 mandatory capability/aggregate facets.

The existing C1302 policy container mixes exempt character-format cases
with a nonexempt FORMAT-statement case. It is left untouched; the stronger
legacy rejection policy is not silently universalized. Likewise, legacy
`S15.5.2.4` is actually anchored in 15.5.2.5 p2-p3, and its fixed kind-number
premises are not portable unsupported-kind witnesses. These are parent
review matters, not permission to change shared fixtures in this batch.

<!-- BEGIN GENERATED 4.2 -->

### S4.2-001: Execute conforming programs within qualified processor limits

**Source:** 4.2 p2(1); J3/24-007 PDF 46, printed 32, lines 9-11; qualifications in p5-p6, PDF 46-47. **Class:** Effect.

**Definition:** The processor must execute standard-conforming programs according to the document's
interpretations, subject to the size and complexity limits it may impose. This is a real
universal processor obligation, not a definition of notation. It does not promise
identical execution across processors or supply missing non-Fortran dependencies.
Processor-dependent facilities retain their qualified methods or semantics under p6.

**Diagnostic obligation:** not-required.

**Facets:** `whole-suite-execution`.

**Oracle limitation:** No executable case or completion credit is assigned to this universal facet. The finite
execution ledger binds the current whole collected case set, including separately
classified negative/admission/context evidence. A partial invocation cannot silently
shrink that set. An aggregate's current source/inventory review is not source
completeness, successful execution, or an independent effect test; the ordinary cases
retain their primary R/C/S owners. Documentation is a proposed way to qualify evidence,
not a conversion of p7-p8 recommendations into mandatory processor documentation.

**Dependencies:** 4.2 p1 distinguishes program and program-unit conformance; 5.2.1-.2 (PDF 56) includes
non-Fortran-defined entities and requires exactly one main program. 4.2 p5 spans PDF 46
lines 42-43 and PDF 47 lines 1-2. Paragraphs 6-8 (PDF 47 lines 3-11) preserve
processor-dependent semantics and documentation modality.

### S4.2-002: Capability to report syntactically detectable obsolescent usage

**Source:** 4.2 p2(2), qualified by p3; J3/24-007 PDF 46, printed 32, lines 12-14 and 33-34. **Class:** Effect.

**Definition:** The processor must have a capability to detect and report obsolescent forms in a
submitted program unit insofar as numbered syntax rules and constraints make their use
detectable. Obsolescent does not mean deleted or nonconforming. Paragraph 3 removes the
obligation to detect or report such usage inside a format specification that is not part
of a FORMAT statement. It does not forbid a processor from reporting it.

**Diagnostic obligation:** required.

**Facets:** `obsolescent-reporting-capability`.

**Oracle limitation:** No invalid-input fixture, generic warning allowance, or requirement to reject
obsolescent syntax is invented. A report absent in one invocation does not by itself
prove absence of the processor capability. Reading the Annex B introduction or the
small-type convention does not approve every obsolescent feature.

**Dependencies:** 4.1.5 p1 identifies smaller-type descriptions; 4.4.3 p2 (PDF 52) refers back to it.
B.3.1 (PDF 577) lists obsolescent features but is not individually catalogued here.
13.2.1-.2 (PDF 289) distinguishes FORMAT statements from character-supplied format
specifications.

### S4.2-003: Capability to report violations of numbered syntax and constraints

**Source:** 4.2 p2(3), qualified by p3; J3/24-007 PDF 46, printed 32, lines 15-17 and 33-34; 4.1.2 p3, PDF 45 lines 7-12. **Class:** Effect.

**Definition:** The processor must have a capability to detect and report forms or relationships in a
submitted program unit that the numbered syntax rules or constraints do not permit,
including deleted features described in Annex B. This does not require every prose
restriction to be diagnosed, nor does it supersede the other explicit p2 reporting
categories. For a format specification outside a FORMAT statement, p3 exempts deleted
features and additional forms or relationships from required detection/reporting. The
exemption does not make an invalid format conforming.

**Diagnostic obligation:** required.

**Facets:** `syntax-reporting-capability`, `constraint-reporting-capability`, `deleted-feature-reporting-capability`.

**Oracle limitation:** No executable case is credited here. The existing C1302 character-format negatives
deliberately use oracle_basis=lfortran-policy and are not mandatory-detection evidence.
The same legacy container also contains a FORMAT-statement case; its source has a
standard reporting obligation, but its stronger rejection contract and shared metadata
are left unchanged for parent review.

**Dependencies:** 4.1.1 requires constraints and text in addition to the displayed BNF; 4.1.2 p2-p3
propagates associated constraints without numbering every prose restriction.
13.2.1/R1301-R1302 and 13.2.2 p1 (PDF 289), plus 13.3.1/C1302 (PDF 290), supply the
exact format boundary. Annex B explicitly identifies deleted features (PDF 576-577); its
individual items remain outside this catalogue.

### S4.2-004: Capability to report unsupported intrinsic kind values

**Source:** 4.2 p2(4); J3/24-007 PDF 46, printed 32, lines 18-19. **Class:** Effect.

**Definition:** For a submitted program unit, the processor must have a capability to detect and report
an intrinsic type used with a kind type parameter value that it does not support. Kind
support is processor-specific and type-specific. Unsupported representation is distinct
from disagreement between two supported kinds in a user-procedure call.

**Diagnostic obligation:** required.

**Facets:** `unsupported-kind-reporting-capability`.

**Oracle limitation:** No guessed kind value, optional-kind skip, or dummy-argument mismatch is presented as
this obligation's test. Legacy S15.5.2.4 cases address actual 15.5.2.5 p2-p3 prose and
retain their independent LFortran policy basis; they are not renamed or counted here.

**Dependencies:** 7.4.1/R704-R706/C717 (PDF 80) and 7.4.4.2/R721/C724 (PDF 84) distinguish intrinsic kinds
and supported representation methods. 15.5.2.5 p1 begins on PDF 339; p2-p3 are on PDF
340 lines 1-10, not in 15.5.2.4.

### S4.2-005: Capability to report prohibited source form and characters

**Source:** 4.2 p2(5); J3/24-007 PDF 46, printed 32, lines 20-21; p3, lines 33-34 where applicable. **Class:** Effect.

**Definition:** The processor must have a capability to detect and report source-form or character usage
in a submitted program unit that Clause 6 does not permit. The obligation is not limited
to restrictions carrying R/C numbers. Establish the selected source form, the
processor's character representation and the actual prohibited context before judging a
witness. Preserve the p3 exemption for additional forms or relationships inside a
non-FORMAT format specification where relevant.

**Diagnostic obligation:** required.

**Facets:** `source-form-reporting-capability`, `source-character-reporting-capability`.

**Oracle limitation:** No new source-form/character fixtures are duplicated here. The existing diagnose
contract can observe justified invalid-input reports, including tightly qualified
nonfatal messages, but cannot certify source-interface documentation or whole-Clause-6
capability.

**Dependencies:** 6.1.1 (PDF 67) partitions the processor character set; 6.1.6 (PDF 68) restricts
additional-character contexts. 6.3 and 6.4 (PDF 71-74) distinguish source forms, actual
statements and INCLUDE lines. Those catalogues and the separate INCLUDE work unit retain
their owners.

### S4.2-006: Capability to report Clause 19 scope inconsistencies

**Source:** 4.2 p2(6); J3/24-007 PDF 46, printed 32, lines 22-23. **Class:** Effect.

**Definition:** The processor must have a capability to detect and report name usage in a submitted
program that conflicts with Clause 19 scope rules for names, labels, operators or
assignment symbols. The submission scope here is a program, unlike the program-unit
wording of most neighboring items. This is not a promise that every inconsistency can be
discovered while compiling an isolated source file.

**Diagnostic obligation:** required.

**Facets:** `name-scope-reporting-capability`, `label-scope-reporting-capability`, `operator-scope-reporting-capability`, `assignment-scope-reporting-capability`.

**Oracle limitation:** All four aggregate facets remain pending. No single-source test is relabeled as proof of
whole-program diagnosis, and prose scope restrictions are not excluded merely because
they lack numbered constraints.

**Dependencies:** 19.1 p2 (PDF 548 lines 4-10) distinguishes identifier scopes and nested/inaccessible
exceptions; 19.2 (PDF 548 lines 23-32) introduces global identifiers. Detailed 19.3-19.5
obligations remain to be catalogued under their own owners. 5.2.2 (PDF 56) defines the
complete program.

### S4.2-007: Capability to report nonstandard intrinsic procedures

**Source:** 4.2 p2(7); J3/24-007 PDF 46, printed 32, lines 24-26. **Class:** Effect.

**Definition:** The processor must have a capability to detect and report use of a nonstandard intrinsic
procedure in a submitted program unit. This explicitly includes a procedure sharing a
standard intrinsic's name but having different requirements. The reporting capability
remains required even when the processor permits the extension.

**Diagnostic obligation:** required.

**Facets:** `additional-intrinsic-reporting-capability`, `altered-intrinsic-reporting-capability`.

**Oracle limitation:** No processor-specific intrinsic is guessed. An external procedure sharing an intrinsic
spelling is not automatically a use of a nonstandard intrinsic. The p4 name-conflict
permission and EXTERNAL protection must be resolved before any fixture is authored.

**Dependencies:** 4.2 p4 (PDF 46 lines 35-41) governs permitted intrinsic additions and program
restrictions. 8.5.9 (PDF 128) specifies EXTERNAL. Clause 16 retains ownership of the
standard intrinsic requirements; this catalogue does not approve that inventory.

### S4.2-008: Capability to report nonstandard intrinsic modules

**Source:** 4.2 p2(8); J3/24-007 PDF 46, printed 32, lines 27-28. **Class:** Effect.

**Definition:** The processor must have a capability to detect and report use of a nonstandard intrinsic
module in a submitted program unit. A missing nonintrinsic module or arbitrary
unresolved USE name is not evidence of this obligation.

**Diagnostic obligation:** required.

**Facets:** `nonstandard-module-reporting-capability`.

**Oracle limitation:** No executable case is assigned without an intrinsic-module identity premise. Neither
successful USE of a standard module nor failure to locate an arbitrary module
establishes this capability.

**Dependencies:** 14.2.1 p1 (PDF 317 lines 19-22) distinguishes processor-provided intrinsic modules from
nonintrinsic modules. 4.2 p4 separately forbids a standard-conforming program from using
a processor-added nonstandard intrinsic module.

### S4.2-009: Capability to report nonstandard procedures in standard intrinsic modules

**Source:** 4.2 p2(9); J3/24-007 PDF 46, printed 32, lines 29-31. **Class:** Effect.

**Definition:** The processor must have a capability to detect and report, in a submitted program unit,
use of a procedure from a standard intrinsic module when the procedure is absent from
this document or has requirements different from those it specifies. This is separate
from using a nonstandard module. A procedure being provided by an intrinsic module does
not itself make that procedure intrinsic.

**Diagnostic obligation:** required.

**Facets:** `additional-module-procedure-reporting-capability`, `altered-module-procedure-reporting-capability`.

**Oracle limitation:** Both facets need non-executable module/interface evidence before meaningful execution
can be designed. They are not folded into the nonstandard-intrinsic-procedure or
nonstandard-module facets.

**Dependencies:** 14.2.1 p2 (PDF 317 line 23) explicitly distinguishes procedures/types in intrinsic
modules from intrinsic entities. The relevant standard module and procedure definitions
in Clauses 16-18 remain separate source owners.

### S4.2-010: Capability to report why a submitted program is rejected

**Source:** 4.2 p2(10); J3/24-007 PDF 46, printed 32, line 32. **Class:** Effect.

**Definition:** The processor must have a capability to detect and report the reason for rejecting a
submitted program. This does not mandate rejection of every nonconforming program, a
particular error code, or fatal severity for the other reporting obligations. It
concerns the reason for a rejection, not just an unsuccessful exit status.

**Diagnostic obligation:** required.

**Facets:** `rejection-reason-reporting-capability`.

**Oracle limitation:** One rejected C401 IF cannot establish all rejection-reason capability. The current
invalid-input reporting contract remains file/line-bound; no runner change or
success-shaped fallback is introduced for general processor reasons.

**Dependencies:** 4.2 p2(1) preserves processor size/complexity limits and p5 preserves out-of-scope
demands. Paragraph 7 recommends documenting limits and their reporting, but that
recommendation is not converted here into a mandatory documentation requirement.

### S4.2-011: Conditions on processor extensions and external-name conflicts

**Source:** 4.2 p4, first three sentences; J3/24-007 PDF 46, printed 32, lines 35-39. **Class:** Restriction.

**Definition:** A processor may add forms and relationships only subject to compatibility with the
standard ones. The explicit exception permits additional intrinsic procedures even when
a procedure name in a standard-conforming program could conflict. For a collision
involving an external procedure, selecting the intrinsic is permitted unless the name
has the EXTERNAL attribute where it is used. That permission does not authorize
overriding a name so declared EXTERNAL. These are conditional restrictions on a
processor that supplies extensions, not a requirement to supply any particular
extension.

**Diagnostic obligation:** not-required.

**Facets:** `extension-compatibility`, `external-attribute-protection`.

**Oracle limitation:** No artificial extension fixture is created. Permission to select an intrinsic without
EXTERNAL is not an obligation to do so. Capability to report extension use is separately
retained in p2(3)/(7)-(9), even when extension acceptance is permitted.

**Dependencies:** 8.5.9 p1 and its constraints (PDF 128) supply the EXTERNAL attribute. 4.2 p1/p4 preserve
conforming-program meaning and distinguish intrinsic use from a same-named external.
Detailed procedure resolution and standard intrinsic semantics stay with their defining
clauses.

### S4.2-012: Conforming programs avoid processor-added nonstandard intrinsics and modules

**Source:** 4.2 p4, final sentence; J3/24-007 PDF 46, printed 32, lines 40-41. **Class:** Restriction.

**Definition:** A standard-conforming program cannot use a processor-added nonstandard intrinsic
procedure or intrinsic module. Acceptance as an extension does not make the program
standard conforming. This restriction does not prohibit an otherwise conforming user
external procedure merely because it shares a spelling with an additional intrinsic;
resolve the p4 name-conflict/EXTERNAL conditions first.

**Diagnostic obligation:** required.

**Facets:** `nonstandard-procedure-use`, `nonstandard-module-use`.

**Oracle limitation:** The required diagnostic basis is explicitly p2(7)-(8), not a blanket rule that every
prose shall implies a compile error. No hello-world is counted as proving that all
conforming programs avoid extensions, and no module-procedure extension is silently
reclassified as an intrinsic procedure.

**Dependencies:** 4.2 p2(7)-(9) distinguishes intrinsic procedures, intrinsic modules and procedures in
standard intrinsic modules. 14.2.1 p1-p2 (PDF 317) and 8.5.9 (PDF 128) provide the
identity and EXTERNAL premises.

### S4.2-013: Provide processor-dependent facilities with processor-determined interpretation

**Source:** 4.2 p6; J3/24-007 PDF 47, printed 33, lines 3-4. **Class:** Effect.

**Definition:** Facilities identified as processor dependent are incompletely specified by the document,
but must nevertheless be provided, using methods or semantics determined by the
processor. Processor dependence is not permission to omit a required facility or to
invent a portable fixed outcome. Conditions and optionality in each facility's defining
source still govern its applicability. The separate p8 documentation recommendation
retains its should modality.

**Diagnostic obligation:** not-required.

**Facets:** `processor-dependent-facility-provision`, `processor-determined-methods-semantics`.

**Oracle limitation:** No context-only program, placeholder zero value, general profile skip or invented
processor-independent oracle is supplied. The current registry cannot express complete
documentary/interface/census aggregation; both facets remain explicit pending work.

**Dependencies:** 4.2 p2(1)/p5 qualifies execution claims; p7-p8 recommends associated documentation.
Existing character-graphics, source-interface and processor-profile gaps remain
separately owned and cannot be closed by this general statement.

<!-- END GENERATED 4.2 -->
