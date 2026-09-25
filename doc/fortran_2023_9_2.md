# Fortran 2023 9.2: Variable

The canonical catalogue is `doc/catalogues/variable_9_2.json`. Effective review state comes from
`Registry.catalogue_review_state("9.2")`; source accounting does not
approve cases, canonical relationships or an execution inventory.

Authority: original J3/24-007, 18 December 2023, 688 pages, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.

Sixteen base units: R902, C901-C902, p1-p2, R903/C903, R904/C904, R905/C905, R906/C906, R907/C907, and the unnumbered note. This source-only packet distinguishes static syntax/constraints from prose definedness and pointer-association requirements.

All facets in this packet are pending source plans. No Fortran test program,
compiler invocation, execution evidence, oracle approval, fixture approval or
coverage claim is supplied here.

<!-- BEGIN GENERATED 9.2 -->

### R902: A variable is a designator or a function reference

**Source:** 9.2 R902, J3/24-007, 18 December 2023, physical PDF150. **Class:** Syntax.

**Definition:** The syntactic category variable is either a designator or a function-reference.
Arbitrary expressions, constants by themselves, procedure names without reference
syntax, and type-parameter inquiries are not additional alternatives.

**Diagnostic obligation:** required.

**Facets:** `designator-variable`, `function-reference-variable`, `expression-not-variable`, `type-parameter-inquiry-boundary`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

R902 data-objects batch300 fixtures: one positive-control program assigns through an
ordinary designator and through an INTEGER data-pointer function reference; one
diagnostic pair rejects an expression and a type-parameter inquiry in
assignment-variable position, with a runtime control that uses ordinary variables.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

R902 data-objects batch300 boundaries: Only the listed batch300 facets are bound. The
fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 4.2;9.1R901/p1;9.4.5R916/C923/note1;15.5.1R1520/C1523-C1524;15.5.3;19.6.5.

### C901: A designator variable is not a constant or constant subobject

**Source:** 9.2 C901, J3/24-007, 18 December 2023, physical PDF150. **Class:** Restriction.

**Definition:** When the R902 variable is a designator, that designator shall not denote a constant and
shall not denote a subobject of a constant. This covers named constants and subobjects
such as elements, components or substrings of constants; it is distinct from the
function-reference alternative.

**Diagnostic obligation:** required.

**Facets:** `named-constant-excluded`, `constant-array-element-excluded`, `constant-structure-component-excluded`, `literal-substring-excluded`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

C901 data-objects batch300 fixtures: one diagnostic/control pair attempts to assign to
an INTEGER named constant and repairs only the PARAMETER attribute. The control mutates
the assignment value and reads it back.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

C901 data-objects batch300 boundaries: Only the listed batch300 facets are bound. The
fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 4.2;6.2.3R604-R607/C602;8.5.13;8.6.11;9.1R901;9.4.1R908-R910/C908;9.4.2;9.5.3.1;19.6.5.

### C902: A function-reference variable has a data pointer result

**Source:** 9.2 C902, J3/24-007, 18 December 2023, physical PDF150. **Class:** Restriction.

**Definition:** When the R902 variable is a function-reference, the referenced function shall have a
data pointer result. A nonpointer data result, a procedure pointer result, or a
subroutine/procedure reference is not this variable alternative.

**Diagnostic obligation:** required.

**Facets:** `data-pointer-result-admission`, `nonpointer-result-excluded`, `procedure-pointer-result-excluded`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

C902 data-objects batch300 fixtures: one positive-control program assigns through three
data-pointer function references serving as the admission case and the one-property
controls for nonpointer and procedure-pointer results. Two negative modules change only
the result category and require a located diagnostic.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

C902 data-objects batch300 boundaries: Only the listed batch300 facets are bound. The
fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 4.2;8.5.14;9.2p1;15.5.1R1520/C1523-C1524;15.5.3;15.6.2.2;19.5.2;19.6.5.

### S9.2-001: A variable denotes a designator object or an associated pointer target

**Source:** 9.2 p1, J3/24-007, 18 December 2023, physical PDF150. **Class:** Effect.

**Definition:** A designator variable is the data object denoted by the designator. A function-reference
variable is the target of the pointer produced by evaluating the function reference, and
that pointer is required to be associated at the reference. The rule identifies the
variable; it does not license reading an undefined target.

**Diagnostic obligation:** not-required.

**Facets:** `designator-denotes-object`, `function-reference-denotes-target`, `associated-pointer-required`.

**Oracle:** Future observations must be complete programs with successful compile/link/run traces,
independent literal or inquiry oracles, executed-path checks and normal completion.
Every referenced variable or target value must be defined by an identified event before
the reference; no address arithmetic, TRANSFER, emitted assembly, compiler agreement or
undefined-storage read is an oracle.

S9.2-001 data-objects batch300 fixtures: one runtime program observes that a designator
denotes its object, a function-reference variable defines the target of the evaluated
associated pointer, and a selected associated pointer target is the variable. Mutants
redirect values or the selected association path.

**Oracle limitation:** These prose requirements are not numbered constraints and do not by themselves impose a
static diagnostic duty. Positive controls show only the planned permitted shape; invalid
undefined-reference executions are not proposed. All entries here are PENDING plans
only; no case, execution, oracle, source-use link, fixture approval or coverage claim is
created.

S9.2-001 data-objects batch300 boundaries: Only the listed batch300 facets are bound.
The fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 9.1R901/p1;9.2R902/C902/p2;15.5.1R1520;15.5.3;19.5.2;19.6.5(1)/(22);19.6.6(16)/(27).

### S9.2-002: A variable reference is permitted only after the variable or data-pointer target is defined

**Source:** 9.2 p2, J3/24-007, 18 December 2023, physical PDF150. **Class:** Effect.

**Definition:** A reference to a variable is permitted only when the variable is defined. A reference to
a data pointer is permitted only when the pointer is associated with a target object
that is defined. The events that define variables with values are those described in
19.6.5; later undefinedness remains governed by 19.6.6.

**Diagnostic obligation:** not-required.

**Facets:** `defined-variable-reference`, `defined-pointer-target-reference`, `definition-event-source`.

**Oracle:** Future observations must be complete programs with successful compile/link/run traces,
independent literal or inquiry oracles, executed-path checks and normal completion.
Every referenced variable or target value must be defined by an identified event before
the reference; no address arithmetic, TRANSFER, emitted assembly, compiler agreement or
undefined-storage read is an oracle.

S9.2-002 data-objects batch300 fixtures: one runtime program references only variables
already defined by intrinsic assignment, a defined associated pointer target, and an
internal WRITE definition event. Mutants change the defining events while preserving
definedness.

**Oracle limitation:** These prose requirements are not numbered constraints and do not by themselves impose a
static diagnostic duty. Positive controls show only the planned permitted shape; invalid
undefined-reference executions are not proposed. All entries here are PENDING plans
only; no case, execution, oracle, source-use link, fixture approval or coverage claim is
created.

S9.2-002 data-objects batch300 boundaries: Only the listed batch300 facets are bound.
The fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 9.1p1;9.2R902/p1;15.5.3;19.6.5;19.6.6.

### R903: A variable name is a name token

**Source:** 9.2 R903, J3/24-007, 18 December 2023, physical PDF150. **Class:** Syntax.

**Definition:** The syntactic form variable-name is name. The rule supplies a name token only; C903 and
the surrounding context determine whether the name denotes a variable.

**Diagnostic obligation:** required.

**Facets:** `single-name-token`, `not-designator-syntax`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

R903 data-objects batch300 fixtures: one namelist positive control reads a scalar
variable-name token and a second scalar name used as the one-property repair for an
array-element namelist object. The invalid fixture supplies the x(1) designator
contrast.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

R903 data-objects batch300 boundaries: Only the listed batch300 facets are bound. The
fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 4.2;6.2.2R603/C601;9.2C903;19.3.

### C903: A variable-name denotes a variable

**Source:** 9.2 C903, J3/24-007, 18 December 2023, physical PDF150. **Class:** Restriction.

**Definition:** A variable-name shall be the name of a variable. A named constant, procedure, derived
type, generic interface, or other non-variable entity does not satisfy this role merely
because it is spelled as a name.

**Diagnostic obligation:** required.

**Facets:** `ordinary-variable-name`, `named-constant-name-excluded`, `procedure-name-excluded`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

C903 data-objects batch300 fixtures: one namelist positive control reads an ordinary
variable-name and observes the assigned value. Named-constant and procedure-name
exclusions remain pending because the frozen LFortran build does not provide suitable
located diagnostics for the planned contrasts.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

C903 data-objects batch300 boundaries: Only the listed batch300 facets are bound. The
fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 4.2;6.2.3R606;8.5.13;8.6.11;9.2R903;15.5.1;19.3.

### R904: A logical-variable is a variable

**Source:** 9.2 R904, J3/24-007, 18 December 2023, physical PDF150. **Class:** Syntax.

**Definition:** The syntactic category logical-variable is the general variable category R902. Its
specific type, if any, is imposed by the paired constraint rather than by a different
variable grammar.

**Diagnostic obligation:** required.

**Facets:** `designator-logical-variable`, `function-reference-logical-variable`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

**Dependencies:** 4.2;9.2R902/p1;15.5.1;19.6.5

### C904: A logical-variable has logical type

**Source:** 9.2 C904, J3/24-007, 18 December 2023, physical PDF150. **Class:** Restriction.

**Definition:** The logical-variable constrained by C904 shall be of type logical. The underlying
variable may be a designator or a qualifying data-pointer function reference, but the
declared/result type must satisfy this constraint.

**Diagnostic obligation:** required.

**Facets:** `logical-type-admission`, `nonlogical-exclusion`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

**Dependencies:** 4.2;7.4.5;9.2R904

### R905: A char-variable is a variable

**Source:** 9.2 R905, J3/24-007, 18 December 2023, physical PDF150. **Class:** Syntax.

**Definition:** The syntactic category char-variable is the general variable category R902. Its specific
type, if any, is imposed by the paired constraint rather than by a different variable
grammar.

**Diagnostic obligation:** required.

**Facets:** `designator-character-variable`, `function-reference-character-variable`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

R905 data-objects batch300 fixtures: one positive-control internal WRITE uses a
CHARACTER designator as the internal-file variable and checks the exact buffer contents
after the write.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

R905 data-objects batch300 boundaries: Only the listed batch300 facets are bound. The
fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 4.2;9.2R902/p1;15.5.1;19.6.5

### C905: A char-variable has character type

**Source:** 9.2 C905, J3/24-007, 18 December 2023, physical PDF150. **Class:** Restriction.

**Definition:** The char-variable constrained by C905 shall be of type character. The underlying
variable may be a designator or a qualifying data-pointer function reference, but the
declared/result type must satisfy this constraint.

**Diagnostic obligation:** required.

**Facets:** `character-type-admission`, `noncharacter-exclusion`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

C905 data-objects batch300 fixtures: one positive-control internal WRITE uses a
CHARACTER variable and checks exact character length and contents, demonstrating the
character-type admission route.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

C905 data-objects batch300 boundaries: Only the listed batch300 facets are bound. The
fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 4.2;7.4.4;9.2R905

### R906: A default-char-variable is a variable

**Source:** 9.2 R906, J3/24-007, 18 December 2023, physical PDF150. **Class:** Syntax.

**Definition:** The syntactic category default-char-variable is the general variable category R902. Its
specific type, if any, is imposed by the paired constraint rather than by a different
variable grammar.

**Diagnostic obligation:** required.

**Facets:** `designator-default-character-variable`, `function-reference-default-character-variable`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

**Dependencies:** 4.2;9.2R902/p1;15.5.1;19.6.5

### C906: A default-char-variable has default character type

**Source:** 9.2 C906, J3/24-007, 18 December 2023, physical PDF150. **Class:** Restriction.

**Definition:** The default-char-variable constrained by C906 shall be of type default character. The
underlying variable may be a designator or a qualifying data-pointer function reference,
but the declared/result type must satisfy this constraint.

**Diagnostic obligation:** required.

**Facets:** `default-character-admission`, `nondefault-character-exclusion`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

**Dependencies:** 4.2;7.4.4.2;9.2R906

### R907: An int-variable is a variable

**Source:** 9.2 R907, J3/24-007, 18 December 2023, physical PDF150. **Class:** Syntax.

**Definition:** The syntactic category int-variable is the general variable category R902. Its specific
type, if any, is imposed by the paired constraint rather than by a different variable
grammar.

**Diagnostic obligation:** required.

**Facets:** `designator-integer-variable`, `function-reference-integer-variable`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

R907 data-objects batch300 fixtures: one ALLOCATE STAT= program uses both an INTEGER
designator and an INTEGER data-pointer function reference as int-variables; exact zero
STAT values are checked after successful allocation.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

R907 data-objects batch300 boundaries: Only the listed batch300 facets are bound. The
fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 4.2;9.2R902/p1;15.5.1;19.6.5

### C907: An int-variable has integer type

**Source:** 9.2 C907, J3/24-007, 18 December 2023, physical PDF150. **Class:** Restriction.

**Definition:** The int-variable constrained by C907 shall be of type integer. The underlying variable
may be a designator or a qualifying data-pointer function reference, but the
declared/result type must satisfy this constraint.

**Diagnostic obligation:** required.

**Facets:** `integer-type-admission`, `noninteger-exclusion`.

**Oracle:** Complete source-qualified compile admissions and minimally repaired, otherwise eligible
contrasts under a qualified F2023 profile. Resolve the actual grammar alternative,
entity role, type, kind, rank, definition status and all overlapping constraints before
assigning a diagnostic cause.

C907 data-objects batch300 fixtures: one ALLOCATE STAT= positive control observes that
an INTEGER variable is accepted and defined with zero on successful allocation.

**Oracle limitation:** The numbered syntax and constraint obligations require detection/reporting capability,
not a fatal exit, rule number or fixed wording. Unsupported syntax, missing prerequisite
declarations or interfaces, unrelated earlier errors, recovery-only messages, source
echoes, crashes and resource failures are not evidence for the stated facet. All entries
here are PENDING plans only; no case, execution, oracle, source-use link, fixture
approval or coverage claim is created.

C907 data-objects batch300 boundaries: Only the listed batch300 facets are bound. The
fixtures assert exact integer, logical, and character properties after explicit
definition, or located diagnostics for numbered syntax/constraint cases that both
retained toolchains report. They do not assert addresses, storage layout,
processor-dependent IOMSG text, coarray behavior, undefined references, generic warning
policy, source review state, or any facet left pending with a batch300 reason.

**Dependencies:** 4.2;7.4.3.1;9.2R907

<!-- END GENERATED 9.2 -->
