# Fortran 2023: 7.8 Construction of array values

**Catalogue source review: independently reviewed. Fixture authoring has not begun.**

**31 base units**, **100 fine units**, **131 accounting rows**, **26 requirements**, and **107 pending facets**. **New cases, executable models and compiler probes: 0.**

## Source-only boundary and exact original binding

This is a **source-reviewed catalogue and unimplemented finite plan**.
Independent source and current-corpus judgments are recorded in
`doc/source_audits/batch_024.json`. No fixture, executable model, compiler
probe, profile or fixture approval is produced.

Authority: J3/24-007, **18 December 2023**, **688 physical PDF pages**, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
Original7.8 on PDF114-116 was read first. PDF117 was used only to check the
actual Clause8 heading. The existing checksum-pinned typography helpers were
then applied only to these bounded original pages. All31 base-unit hashes and
section hash `f4bd8ea5b5740846f5c0bfa5503d17069172239036001096ba44c84fe606978c`
match the committed census. NOTE1-NOTE6 retain their original identities.
Original excerpts remain only in session evidence, not copied into this view.

## Source distinctions and required authoring qualifications

* Matched `(/ ... /)` and `[ ... ]` forms enclose the actual R778 ac-spec.
  Typed-empty syntax is different from untyped inference or a nonempty body
  whose expansion happens to be empty. Empty derived-type arrays need no
  scalar structure-constructor component arguments, but their type-spec still
  satisfies type/access/abstract/parameter constraints.
* Implicit type/KIND agreement is C7120; implicit corresponding LEN agreement
  is the separate p2 prose restriction. Different input ranks/shapes are
  permitted and flattened. There is no longest-character-literal rule.
* Explicit intrinsic/enum type conformance, derived declared-type/KIND equality,
  enumeration identity and full p3 assignment compatibility remain distinct.
  C7121's BOZ alternative never waives C7126/C7127 or global C7119.
* Scalar ac-values contribute one element; arrays contribute all elements in
  array element order to one rank-one result. A matrix is initialized by named
  indices, not another RESHAPE/constructor that could cancel an order defect.
  User defined assignment is not a general constructor coercion.
* The ac-do-variable is a **statement entity**, with its own implied-DO scope,
  scalar INTEGER type/parameters and no other attributes. Inline typing does
  not declare a containing-scope variable. Nested reuse is forbidden; separate
  nonnested uses have separate scopes. Host scalar names may be shadowed, but
  a named constant/array/global-name collision is not the same permission.
* Control initialization/execution follows the ordinary DO rules, not DO
  CONCURRENT. Default step1, nonzero step, typed controls and finite iteration
  counts are kept separate from syntax and constant-expression predicates.
  Bounds use separately defined names, not an uninitialized self-reference.
* Required element sequence is not a prescribed function-evaluation order.
  10.1.4p3's control evaluation,10.1.4's side-effect restrictions,10.1.7's
  optional operand evaluation and19.6.6's resulting undefined statuses are
  retained. No empty-array callback-absence or mutable-counter shortcut is used.
* Zero-trip CHARACTER lengths must satisfy both p5 conditions, including the
  ac-do-variable condition even when10.1.12 permits that index as a constant
  expression. A dynamic LEN on typed-empty syntax has no ac-value and a
  different antecedent. No absent deferred parameter is queried.
* ENUM enumerators are INTEGER; named enum-type values and ordinal ENUMERATION
  TYPE values are different nonintrinsic types. Enum/integer primary provenance,
  same-definition type identity and INT/KIND applicability retain their owners.
* Colon/asterisk parameter contexts, pointer/allocatable value availability,
  limited versus unlimited polymorphism and declared abstractness are checked
  at the actual source role. Neither parent ancestry nor a component's
  polymorphism is a recursive blanket ban on an otherwise ordinary ac-value.

## Reporting, representation and deferred questions

R/C reporting capability follows4.1.2/4.1.3 and4.2p2(3), not fatal rejection,
fixed wording or rule codes. Name-scope and nonstandard intrinsic duties retain
4.2p2(6)/(7). Plain LEN, assignment-compatibility and zero-trip length
restrictions do not acquire automatic fatal-diagnostic policies.
Every prospective negative has a bounded source/repair or an explicit
processor/causal gate. Wrong properties, source echo, generic recovery,
unsupported facilities, Internal/verifier/resource failures, crashes and
timeouts cannot supply another rule's evidence.

BOZsource `c0c9e5de` remains **unapproved** and is not imported as authority.
Only necessary original7.7/16.3/INT/assignment dependencies were read.
C7126's typed INTEGER/REAL requirement is not enough for C7127's REAL validity;
C1601's nonzero discarded bits are a different condition. No C_INT, numeric
KIND identifier, minimum width, IEEE bit layout, invalid NaN or arbitrary
raw-representation oracle is assumed. All existing profiles and the realBOZ
needs-oracle record remain unchanged.

The finite qualifications ACS-Q01 through ACS-Q07 are recorded in the handoff:
evaluation/state, zero-trip length, polymorphic diagnostic isolation,
REAL-BOZ representation, processor kind/parameter context, direct-observer/
canonical-use boundaries, and ordinary numeric approximation. REAL/CMPLX
conversion does not become universally exact through a default-REAL precision
recommendation. No blocking normative source defect is asserted;
conditional concrete designs still require independent review.

## Complete source accounting

### `C7120` (PDF115)

* `C7120`: **requirements** - C7120
* `C7120.type-spec-absent-condition`: **requirements** - C7120
* `C7120.same-declared-type`: **requirements** - C7120
* `C7120.same-kind-parameter-values`: **requirements** - C7120

### `C7121` (PDF115)

* `C7121`: **requirements** - C7121
* `C7121.intrinsic-type-antecedent`: **requirements** - C7121
* `C7121.enum-type-antecedent`: **requirements** - C7121
* `C7121.each-value-type-conformance`: **requirements** - C7121
* `C7121.table10.8-owner`: **requirements** - C7121
* `C7121.conditional-boz-alternative`: **permission** - The BOZ alternative is conditional on all other consumer rules, especially C7126/C7127 and C7119. It does not authorize LOGICAL, CHARACTER or enum typed BOZ constructors. Associated defining owner: C7121.

### `C7122` (PDF115)

* `C7122`: **requirements** - C7122
* `C7122.derived-type-spec-condition`: **requirements** - C7122
* `C7122.each-value-expression`: **requirements** - C7122
* `C7122.same-declared-derived-type`: **requirements** - C7122
* `C7122.matching-kind-tuple`: **requirements** - C7122

### `C7123` (PDF115)

* `C7123`: **requirements** - C7123
* `C7123.enumeration-type-spec-condition`: **requirements** - C7123
* `C7123.same-enumeration-type-values`: **requirements** - C7123

### `C7124` (PDF115)

* `C7124`: **requirements** - C7124
* `C7124.unlimited-polymorphic-ac-value-exclusion`: **requirements** - C7124

### `C7125` (PDF115)

* `C7125`: **requirements** - C7125
* `C7125.declared-abstract-type-exclusion`: **requirements** - C7125

### `C7126` (PDF115)

* `C7126`: **requirements** - C7126
* `C7126.boz-ac-value-condition`: **requirements** - C7126
* `C7126.explicit-type-spec-required`: **requirements** - C7126
* `C7126.integer-or-real-only`: **requirements** - C7126

### `C7127` (PDF115)

* `C7127`: **requirements** - C7127
* `C7127.boz-ac-value-condition`: **requirements** - C7127
* `C7127.real-type-spec-condition`: **requirements** - C7127
* `C7127.valid-internal-representation`: **requirements** - C7127
* `C7127.specified-real-kind`: **requirements** - C7127

### `C7128` (PDF115)

* `C7128`: **requirements** - C7128
* `C7128.nested-implied-do-condition`: **requirements** - C7128
* `C7128.inner-control-variable`: **requirements** - C7128
* `C7128.containing-control-variable-exclusion`: **requirements** - C7128

### `R777` (PDF114)

* `R777`: **requirements** - R777
* `R777.slash-parenthesis-form`: **requirements** - R777
* `R777.square-bracket-form`: **requirements** - R777

### `R778` (PDF114)

* `R778`: **requirements** - R778
* `R778.typed-empty-alternative`: **requirements** - R778
* `R778.required-double-colon-with-type`: **requirements** - R778
* `R778.optional-type-before-values`: **requirements** - R778
* `R778.nonempty-value-list-alternative`: **requirements** - R778

### `R779` (PDF114)

* `R779`: **requirements** - R779
* `R779.opening-square-bracket`: **requirements** - R779

### `R780` (PDF114)

* `R780`: **requirements** - R780
* `R780.closing-square-bracket`: **requirements** - R780

### `R781` (PDF115)

* `R781`: **requirements** - R781
* `R781.expression-alternative`: **requirements** - R781
* `R781.implied-do-alternative`: **requirements** - R781

### `R782` (PDF115)

* `R782`: **requirements** - R782
* `R782.parenthesized-form`: **requirements** - R782
* `R782.nonempty-body-value-list`: **requirements** - R782
* `R782.comma-before-control`: **requirements** - R782
* `R782.implied-do-control`: **requirements** - R782

### `R783` (PDF115)

* `R783`: **requirements** - R783
* `R783.optional-integer-type-spec`: **requirements** - R783
* `R783.type-spec-double-colon`: **requirements** - R783
* `R783.control-variable-and-equals`: **requirements** - R783
* `R783.initial-scalar-integer`: **requirements** - R783
* `R783.terminal-scalar-integer`: **requirements** - R783
* `R783.optional-increment`: **requirements** - R783
* `R783.control-separators`: **requirements** - R783

### `R784` (PDF115)

* `R784`: **requirements** - R784
* `R784.do-variable-name`: **requirements** - R784

### `note1` (PDF116)

* `note1`: **informative** - Original NOTE1 on PDF116 is an illustrative RESHAPE consumer and displayed matrix, not a new local RESHAPE requirement.
* `note1.rank-one-constructor-inputs`: **informative** - The constructors in the RESHAPE example are rank one; nested array-valued expressions contribute an element sequence.
* `note1.reshape-has-separate-owner`: **informative** - RESHAPE supplies the allowable rank-two shape; the constructor does not itself acquire that shape.
* `note1.illustrated-matrix-order`: **informative** - The displayed3-by-2 values use the input sequence2.0,4.5,4.5,3.2,4.01,6.5 in array element order. A future flattening oracle must use independently named inputs, not a second RESHAPE setup/comparison that can cancel the same error.

### `note2` (PDF116)

* `note2`: **informative** - Original NOTE2, PDF116 contains two incomplete-context examples, not extra constraints or a prescribed evaluation order.
* `note2.integer-implied-do-example`: **informative** - The first example illustrates a complete initial/terminal integer sequence through1075; host typing must still be valid in a full context.
* `note2.mixed-scalar-and-loop-example`: **informative** - The second example combines one scalar REAL value and an implied-DO contribution.
* `note2.n-and-variable-context`: **informative** - N and I need their actual type/definition/scope premises; the fragment is not an undefined-bound, division-trap or callback-order oracle.

### `note3` (PDF116)

* `note3`: **informative** - Original NOTE3 is the PERSON derived-array illustration.
* `note3.derived-scalar-element-values`: **informative** - PERSON scalar structure-constructor values form the derived-type array.
* `note3.person-definition-and-constructor-owners`: **informative** - The cited PERSON definition and7.5.10 access/component/type conditions remain necessary. This example does not approve every structure constructor or type identity by layout.

### `note4` (PDF116)

* `note4`: **informative** - Original NOTE4 illustrates nested constructor/RESHAPE consumers and keeps the outer scalar/inner array distinction.
* `note4.inner-array-constructor`: **informative** - The inner list constructs a rank-one REAL sequence.
* `note4.reshape-to-rank-two-component`: **informative** - RESHAPE changes that sequence to the component's2-by-2 array value.
* `note4.outer-line-is-scalar-structure`: **informative** - LINE constructs a scalar derived value with an array component; it is not a rank-two array constructor.
* `note4.application-units-example`: **informative** - Line coordinates, width0.1 and solid-pattern interpretation are example/application context, not an internal REAL layout or new local effect oracle.

### `note5` (PDF116)

* `note5`: **informative** - Original NOTE5 gives two distinct ways to obtain zero size, without waiving inference, scope or loop conditions.
* `note5.typed-empty-example`: **informative** - [INTEGER ::] illustrates R778's typed-empty alternative.
* `note5.zero-trip-example`: **informative** - [(I,I=1,0)] has a nonempty ac-value-list with an empty expansion; it is not the same syntax as untyped[].
* `note5.implicit-do-typing-context`: **informative** - A complete IMPLICIT NONE context must declare the appropriate containing INTEGER name or use inline INTEGER specification. The fragment does not implicitly declare a host variable.

### `note6` (PDF116)

* `note6`: **informative** - Original NOTE6 demonstrates explicit CHARACTER length and the separate implicit-LEN restriction.
* `note6.explicit-character-length`: **informative** - CHARACTER(LEN=7) fixes the constructor length.
* `note6.different-source-lengths`: **informative** - The six/six/seven-character source literals may be used under that explicit length.
* `note6.omitted-type-needs-length-agreement`: **informative** - Without the type-spec their differing lengths would violate p2, not a type/kind mismatch under C7120. The example does not choose a longest-string inference rule.

### `p1` (PDF114)

* `p1`: **structural** - Original PDF114: fine accounting separates every condition, definition, effect and source-use premise.
* `p1.array-value-result`: **requirements** - S7.8-001
* `p1.rank-one-result`: **requirements** - S7.8-001
* `p1.scalar-value-source-class`: **definition** - Scalar values are one source category; R781 and p6 specify their actual contribution.
* `p1.array-value-source-class`: **definition** - Array values are permitted sources; their input rank does not become the result rank.
* `p1.implied-do-source-class`: **definition** - Implied DO is the third source category; it is not a DO CONCURRENT construct.

### `p2` (PDF115)

* `p2`: **structural** - Original PDF115: fine accounting separates every condition, definition, effect and source-use premise.
* `p2.type-spec-omitted`: **requirements** - S7.8-002, S7.8-003
* `p2.corresponding-length-parameters`: **requirements** - S7.8-002
* `p2.length-values-agree`: **requirements** - S7.8-002
* `p2.inferred-declared-type`: **requirements** - S7.8-003
* `p2.inferred-type-parameter-values`: **requirements** - S7.8-003

### `p3` (PDF115)

* `p3`: **structural** - Original PDF115: fine accounting separates every condition, definition, effect and source-use premise.
* `p3.type-spec-present`: **requirements** - S7.8-003, S7.8-004, S7.8-005
* `p3.specified-declared-type-and-parameters`: **requirements** - S7.8-003
* `p3.every-expression-intrinsic-assignment-compatible`: **requirements** - S7.8-004
* `p3.each-value-converted`: **requirements** - S7.8-005
* `p3.intrinsic-assignment-conversion-rules`: **requirements** - S7.8-005

### `p4` (PDF115)

* `p4`: **requirements** - S7.8-006
* `p4.constructor-dynamic-type`: **requirements** - S7.8-006
* `p4.same-as-declared-type`: **requirements** - S7.8-006

### `p5` (PDF115)

* `p5`: **requirements** - S7.8-007
* `p5.character-ac-value-in-implied-do`: **requirements** - S7.8-007
* `p5.zero-iteration-count-condition`: **requirements** - S7.8-007
* `p5.length-independent-of-ac-do-variable`: **requirements** - S7.8-007
* `p5.length-independent-of-nonconstant-expression`: **requirements** - S7.8-007

### `p6` (PDF115)

* `p6`: **structural** - Original PDF115: fine accounting separates every condition, definition, effect and source-use premise.
* `p6.scalar-expression-condition`: **requirements** - S7.8-001
* `p6.one-element-from-scalar`: **requirements** - S7.8-001
* `p6.array-expression-condition`: **requirements** - S7.8-001
* `p6.array-elements-in-array-element-order`: **requirements** - S7.8-001
* `p6.corresponding-sequence-contribution`: **requirements** - S7.8-001
* `p6.implied-do-expansion`: **requirements** - S7.8-008
* `p6.ac-do-variable-control-as-do`: **requirements** - S7.8-008

### `p7` (PDF115)

* `p7`: **structural** - Original PDF115: fine accounting separates every condition, definition, effect and source-use premise.
* `p7.implied-do-initialization`: **requirements** - S7.8-008
* `p7.implied-do-execution`: **requirements** - S7.8-008
* `p7.same-as-do-construct`: **requirements** - S7.8-008
* `p7.scope-and-attributes-canonical-reference`: **definition** - 19.4 supplies statement-entity scope, INTEGER type/parameters and no other attributes. The ac-do variable is not a construct entity, not a containing-scope declaration, and not an I/O implied-DO variable whose host value is reused.

### `p8` (PDF115)

* `p8`: **requirements** - S7.8-009
* `p8.empty-sequence-condition`: **requirements** - S7.8-009
* `p8.zero-sized-array-result`: **requirements** - S7.8-009

## Definitions

<!-- BEGIN GENERATED 7.8 -->

### R777: Array constructors have matched slash-parenthesis or square-bracket delimiters

**Source:** 7.8, R777; J3/24-007, 18 December 2023, physical PDF 114. **Class:** Syntax.

**Definition:** An array constructor encloses an ac-spec either in (/ and /) or in [ and ]. The two
matched forms are alternatives; the ac-spec conditions apply to both.

**Diagnostic obligation:** required.

**Facets:** `slash-parenthesis-admission`, `square-bracket-admission`, `mismatched-closing-delimiter`, `type-and-value-consumer-source-use`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R778-R780;4.1.3;R702;7.8p1/p6/p8;4.2p2(3).

### R778: An ac-spec is typed-empty or a nonempty value list with optional type

**Source:** 7.8, R778; J3/24-007, 18 December 2023, physical PDF 114. **Class:** Syntax.

**Definition:** An ac-spec is either type-spec followed by :: with no values, or a nonempty
ac-value-list optionally preceded by type-spec ::. An omitted type does not permit a
syntactically empty list. Type-spec is the R702 category, not every R703
declaration-type-spec alternative.

**Diagnostic obligation:** required.

**Facets:** `typed-empty-integer`, `typed-empty-other-categories`, `typed-nonempty`, `untyped-nonempty`, `untyped-empty-list`, `type-spec-parameter-context-graph`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R702/R703;R781/R401;7.2/C701/C702;7.4.4.2/C726;7.5.9/C795-C7100;C7120-C7127;7.8p2-p5/p8.

### R779: The lbracket token is the opening square bracket

**Source:** 7.8, R779; J3/24-007, 18 December 2023, physical PDF 114. **Class:** Syntax.

**Definition:** In the array-constructor syntax, lbracket denotes the [ token.

**Diagnostic obligation:** required.

**Facets:** `opening-bracket-source-use`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R777;6.1.5 and6.2.6;4.2p2(3)/(5).

### R780: The rbracket token is the closing square bracket

**Source:** 7.8, R780; J3/24-007, 18 December 2023, physical PDF 114. **Class:** Syntax.

**Definition:** In the array-constructor syntax, rbracket denotes the ] token.

**Diagnostic obligation:** required.

**Facets:** `closing-bracket-source-use`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R777;6.1.5 and6.2.6;4.2p2(3)/(5).

### R781: An ac-value is an expression or an ac-implied-do

**Source:** 7.8, R781; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Syntax.

**Definition:** Each ac-value is an expression or an ac-implied-do. The expression may be scalar or
array-valued; its permitted type/state and sequence contribution are separate
conditions.

**Diagnostic obligation:** required.

**Facets:** `scalar-expression-admission`, `array-expression-admission`, `implied-do-admission`, `expression-category-and-state-graph`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R782-R784;C7120-C7127;7.8p6;9.7.1;10.1.9/10.1.12;19.6.

### R782: An ac-implied-do contains a nonempty value list and its control

**Source:** 7.8, R782; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Syntax.

**Definition:** An ac-implied-do encloses a nonempty ac-value-list, a separating comma and an
ac-implied-do-control in parentheses. Nested implied DOs are allowed subject to C7128.

**Diagnostic obligation:** required.

**Facets:** `single-body-value`, `multiple-body-values`, `nested-form`, `missing-control-separator`, `missing-body-list`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R781/R783/R784;R401;C7128;19.4p1-p2/p5;4.2p2(3).

### R783: Implied-DO controls have optional INTEGER specification and scalar integer bounds

**Source:** 7.8, R783; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Syntax.

**Definition:** The control optionally starts with integer-type-spec ::, then gives the ac-do-variable,
=, an initial scalar INTEGER expression, a terminal scalar INTEGER expression, and
optionally an increment scalar INTEGER expression. Runtime controls need not be
constant.

**Diagnostic obligation:** required.

**Facets:** `inferred-integer-variable`, `inline-default-integer`, `inline-supported-kind`, `required-two-bounds`, `integer-and-scalar-bound-conditions`, `runtime-bound-and-step-expressions`, `loop-execution-and-zero-step-source-use`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R784/R1124/C1121;4.1.3/C401;10.1.9.1/R1027/C1009;10.1.12;11.1.7.4.1/.3;19.4p5.

### R784: An ac-do-variable uses the scalar integer DO-variable name syntax

**Source:** 7.8, R784; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Syntax.

**Definition:** An ac-do-variable is a do-variable, whose canonical syntax is a scalar INTEGER variable
name. Its type/parameters and restricted scope are those of the statement entity defined
by19.4, not an arbitrary writable designator.

**Diagnostic obligation:** required.

**Facets:** `bare-scalar-integer-name`, `literal-is-not-control-variable`, `scope-and-designator-consumer-graph`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R1124/C1121, PDF210;19.4p1-p2/p5, PDF551;4.2p2(3)/(6).

### C7120: Without type-spec all ac-value expressions have matching declared types and KIND parameters

**Source:** 7.8, C7120; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** When type-spec is absent, each ac-value expression has the same declared type and
corresponding kind type parameter values. This is not a requirement that their ranks,
shapes, numerical values or corresponding LEN parameters be identical; p2 separately
governs LEN agreement.

**Diagnostic obligation:** required.

**Facets:** `same-type-kind-different-ranks`, `different-intrinsic-type`, `different-supported-intrinsic-kinds`, `different-derived-kind-tags`, `declared-dynamic-length-and-identity-source-use`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** 7.3.2.3/7.3.3;7.5.3;7.6;7.8p2/p4/p6;C7124/C7125;4.2p2(3).

### C7121: Explicit intrinsic or enum type requires Table10.8 type conformance or the qualified BOZ alternative

**Source:** 7.8, C7121; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** If type-spec names an intrinsic type or enum type, every ac-value expression has a type
conforming with a variable of that type under Table10.8, or is BOZ. This disjunction
does not waive C7126/C7127, intrinsic-assignment compatibility in p3, or the correct
defining-enum primary condition for INTEGER expressions.

**Diagnostic obligation:** required.

**Facets:** `intrinsic-type-admissions`, `intrinsic-type-mismatch`, `enum-correct-primary-admission`, `enum-wrong-integer-provenance`, `boz-conjunction-and-char-kind-graph`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** 10.2.1.2/Table10.8, PDF189;7.3.3;7.6.1;7.8p3;C7126/C7127;7.7/C7119.

### C7122: Explicit derived type requires that declared type and its KIND parameters for every expression

**Source:** 7.8, C7122; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** When type-spec specifies a derived type, each ac-value expression has that declared
derived type and the kind type parameter values specified by type-spec. Dynamic
extension identity or an available defined assignment is not a substitute; LEN
compatibility remains a separate p3 condition.

**Diagnostic obligation:** required.

**Facets:** `same-derived-type-admission`, `different-declared-type`, `different-user-kind-parameter`, `declared-not-dynamic-and-len-graph`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** 7.3.2.3;7.5.3;7.8p3/p4;C703/C7125;10.2.1.2p1(9)-(10);7.5.10.

### C7123: Explicit enumeration type admits only values of that enumeration type

**Source:** 7.8, C7123; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** When type-spec specifies an enumeration type, each ac-value is of that type. An INTEGER
ordinal or an interoperable ENUM enumerator is not itself a value of that enumeration
type, and equal ordinals from different definitions do not establish type identity.

**Diagnostic obligation:** required.

**Facets:** `same-enumeration-admission`, `integer-is-not-enumeration`, `other-enumeration-type`, `identity-and-constructor-source-use`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** 7.6.2p1/p3-p5;R702/R770/R771/C7116;7.8p3;10.2.1.2/Table10.8.

### C7124: An ac-value cannot be unlimited polymorphic

**Source:** 7.8, C7124; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** An ac-value cannot be unlimited polymorphic. The restriction is on the ac-value itself;
it is not a recursive prohibition on every component of an ordinary derived-type value
or a ban on using CLASS(*) elsewhere in the program.

**Diagnostic obligation:** required.

**Facets:** `limited-value-admissions`, `unlimited-value-focused-contrast`, `outer-value-versus-component-source-use`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7). An explicit typed constructor can add a separate type-conformance
defect for CLASS(*); keep that out of the proposed focused contrast.

**Dependencies:** R781;7.3.2.3p4-p5;11.1.11.2p5, PDF226;19.4p12;15.5.2.4-.5;4.2p2(3).

### C7125: An ac-value's declared type cannot be abstract

**Source:** 7.8, C7125; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** The declared type of an ac-value must not be abstract, even when its dynamic type is a
concrete extension. A concrete declared child with an abstract parent is not excluded
merely by that ancestry. C703 separately constrains an explicit abstract type-spec.

**Diagnostic obligation:** required.

**Facets:** `declared-abstract-contrast`, `concrete-child-admission`, `type-spec-and-temporary-source-use`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R781;C703/C706;7.5.7.1/C738/C739;7.8p4;15.5.2.4-.5;4.2p2(3).

### C7126: A BOZ ac-value requires an explicit INTEGER or REAL type-spec

**Source:** 7.8, C7126; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** If an ac-value is BOZ, type-spec must be present and must specify INTEGER or REAL.
Typeless BOZ is not a general INTEGER expression. C7121's BOZ alternative does not
permit any other intrinsic type, enum type or enumeration type.

**Diagnostic obligation:** required.

**Facets:** `typed-integer-boz-admission`, `typed-real-qualified-admission`, `omitted-type-spec`, `wrong-type-spec`, `nested-boz-and-allowed-use-source-use`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** 7.7/C7119, PDF114;C7121/C7127;7.8p3;16.3.3/C1601;10.2.1.3p9;4.2p2(3).

### C7127: A REAL BOZ ac-value needs a valid representation for that REAL kind

**Source:** 7.8, C7127; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** When a BOZ ac-value is paired with a REAL type-spec, the bit sequence must be a valid
internal representation for the specified REAL kind. The requirement is processor/kind
dependent and is not established by lexical BOZ validity, C7119 admission,
arithmetic-model inquiries alone or acceptance by another compiler.

**Diagnostic obligation:** required.

**Facets:** `valid-pattern-documentary-gate`, `invalid-pattern-diagnostic-gate`, `real-boz-and-truncation-owner-graph`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** C7126;7.7;16.3.1/.3/C1601, PDF365-366;10.2.1.3p9/Table10.9;16.9 INT/REAL
specifications;4.2p2(3).

### C7128: Nested ac-implied-do controls cannot reuse the containing variable

**Source:** 7.8, C7128; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** The ac-do-variable of an implied DO nested in another ac-implied-do must not also appear
as the containing implied DO's ac-do-variable. Separate nonnested implied DOs have
separate scopes; this is not a ban on all reuse of a spelling.

**Diagnostic obligation:** required.

**Facets:** `nested-same-name`, `distinct-nested-variables`, `disjoint-reuse-admission`.

**Oracle:** Source-only diagnostic plans require complete otherwise-conforming contexts and a
focused legal repair. Numbered reporting capability follows4.1.2/4.1.3 and4.2p2(3), not
mandatory fatal rejection, a fixed severity or printed rule codes. Actual contracts must
identify the intended source role/property, file, statement and causal relation after
source review.

**Oracle limitation:** No diagnostic contract or test is authored. Wrong type/kind/rank/length/name properties,
source echo, generic EOF/missing-END recovery, unsupported facilities, compiler
internal/verifier/resource failures, crashes and timeouts cannot corroborate another
condition. Scope-name reporting remains4.2p2(6); intrinsic-procedure misuse
retains4.2p2(7).

**Dependencies:** R782-R784;19.4p1-p2/p5, PDF551;4.2p2(3)/(6).

### S7.8-001: Construction produces a rank-one sequence of scalar and flattened array values

**Source:** 7.8, p1, p6; J3/24-007, 18 December 2023, physical PDF 114, 115. **Class:** Effect.

**Definition:** An array constructor produces a rank-one array value. A scalar ac-value contributes one
element; an array ac-value contributes all its elements in array element order to the
corresponding positions of the result sequence. Input rank/shape is not the rank/shape
of the constructor, and sequence placement does not prescribe side-effect evaluation
order.

**Diagnostic obligation:** not-required.

**Facets:** `rank-one-and-scalar-sequence`, `higher-rank-flattening`, `mixed-shapes-and-empty-source`, `value-expression-state-source-use`, `evaluation-order-and-shared-consumer-graph`.

**Oracle:** Use distinct small integer markers, independently assigned named source elements and
direct constructor value/rank/size observations. Permitted array element order fixes
sequence positions, not the order of evaluating unrelated source functions.

**Oracle limitation:** No runtime witness is implemented. Use independently fixed small values, named element
setup and direct constructor observations; a destination declaration or a second use of
the same operation is not an independent oracle. Source sequence order is not an
unspecified function-evaluation order. Read only defined values with established
allocation/association and valid parameter state. No C_INT, KIND-number, extra-kind,
byte-width, IEEE-layout, arbitrary-bit or processor-choice premise is assumed.

**Dependencies:** 7.8p1/p6;9.5.3.3/Table9.1;10.1.4/10.1.7;7.5.8/7.5.10;9.7.1;19.6.1-.2;16.9.171
RANK/16.9.194 SIZE.

### S7.8-002: Untyped inference requires corresponding LEN parameter values to agree

**Source:** 7.8, p2; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** If type-spec is omitted, corresponding length type parameter values of the declared
types of the ac-value expressions must agree. This includes CHARACTER length and derived
LEN parameters, separately from C7120's type/KIND condition. It is a prose restriction,
not a new automatic diagnostic or longest-length rule.

**Diagnostic obligation:** not-required.

**Facets:** `character-length-source-contrast`, `derived-len-source-contrast`, `runtime-equal-length-controls`, `zero-size-and-explicit-spec-boundaries`.

**Oracle:** Valid same-LEN controls are positive controls. Any desired diagnostic for differing
lengths needs a separately approved policy and an otherwise valid source-minimal repair;
no such policy is created here.

**Oracle limitation:** No runtime witness is implemented. Use independently fixed small values, named element
setup and direct constructor observations; a destination declaration or a second use of
the same operation is not an independent oracle. Source sequence order is not an
unspecified function-evaluation order. Read only defined values with established
allocation/association and valid parameter state. No C_INT, KIND-number, extra-kind,
byte-width, IEEE-layout, arbitrary-bit or processor-choice premise is assumed.

**Dependencies:** C7120;7.8p2/p3/p5;7.2;7.4.4.2;7.5.3;9.7.1;16.9.122 LEN;4.1.2p3/4.2.

### S7.8-003: Declared result type and parameters are inferred or supplied by type-spec

**Source:** 7.8, p2, p3; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Effect.

**Definition:** With type-spec omitted, the constructor's declared type and type parameter values are
those of its conforming ac-value expressions. With type-spec present, that specifier
determines the constructor's declared type and parameters. Neither source array rank nor
a destination's allocation/parameter attributes redefine the constructor.

**Diagnostic obligation:** not-required.

**Facets:** `inferred-integer-kind`, `inferred-character-length`, `explicit-type-and-runtime-length`, `nonintrinsic-identity-consumer-source-use`, `deferred-assumed-and-destination-boundary`.

**Oracle:** Only the finite source-supported value/type/parameter observations below are planned.
Their independent literals, complete state and actual constructor consumers must be
checked before fixture authoring.

**Oracle limitation:** No runtime witness is implemented. Use independently fixed small values, named element
setup and direct constructor observations; a destination declaration or a second use of
the same operation is not an independent oracle. Source sequence order is not an
unspecified function-evaluation order. Read only defined values with established
allocation/association and valid parameter state. No C_INT, KIND-number, extra-kind,
byte-width, IEEE-layout, arbitrary-bit or processor-choice premise is assumed.

**Dependencies:** 7.8p2/p3;R778/R702;7.2/C701/C702;7.4.4.2/C726;7.5.9/C7100;7.6;16.9.118 KIND/16.9.122
LEN;8.5.3.

### S7.8-004: Explicit type-spec also requires full intrinsic-assignment compatibility

**Source:** 7.8, p3; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** When type-spec appears, each ac-value expression must be compatible with intrinsic
assignment to a variable of that type and type parameters. The complete relationship is
broader than the numbered type/KIND constraints alone. It does not mean all ac-value
arrays must have one shape, and it does not authorize arbitrary defined-assignment
coercion.

**Diagnostic obligation:** not-required.

**Facets:** `fixed-derived-len-compatibility`, `character-kind-domain-qualification`, `defined-assignment-is-not-coercion`, `shape-pointer-and-consumer-boundaries`.

**Oracle:** Preserve the full assignment-compatibility premise without creating a new mandatory
prose-diagnostic policy. Valid finite cases are positive controls; overlapping numbered
type conditions are not relabelled.

**Oracle limitation:** No runtime witness is implemented. Use independently fixed small values, named element
setup and direct constructor observations; a destination declaration or a second use of
the same operation is not an independent oracle. Source sequence order is not an
unspecified function-evaluation order. Read only defined values with established
allocation/association and valid parameter state. No C_INT, KIND-number, extra-kind,
byte-width, IEEE-layout, arbitrary-bit or processor-choice premise is assumed.

**Dependencies:** 7.8p3;C7121-C7123;10.2.1.2/Table10.8 andp1(7)-(10);10.2.1.3;7.5.10;4.1.2p3/4.2.

### S7.8-005: Explicit constructor values undergo the specified intrinsic conversions

**Source:** 7.8, p3; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Effect.

**Definition:** With explicit type-spec, each value is converted to the constructor's type and type
parameters according to intrinsic assignment. Conversion applies to the contributed
values and is not evidence that a later assignment statement or user defined assignment
performed the constructor's work.

**Diagnostic obligation:** not-required.

**Facets:** `small-numeric-conversion`, `character-padding-and-truncation`, `nonzero-dependent-character-length`, `enum-conversion-source-use`, `boz-conversion-and-representation-gate`.

**Oracle:** Use direct constructor arguments and independent literal observations, not an outer
assignment conversion or a second constructor/RESHAPE. The old numeric/character
assignment cases keep their own primary effects.

**Oracle limitation:** No runtime witness is implemented. Use independently fixed small values, named element
setup and direct constructor observations; a destination declaration or a second use of
the same operation is not an independent oracle. Source sequence order is not an
unspecified function-evaluation order. Read only defined values with established
allocation/association and valid parameter state. No C_INT, KIND-number, extra-kind,
byte-width, IEEE-layout, arbitrary-bit or processor-choice premise is assumed. REAL and
CMPLX have processor-dependent approximation clauses. Default REAL precision6/range37
are recommendations, not general mandatory accuracy bounds. Any exact real/complex
numeric result needs an independently established arithmetic premise, distinct from
internal bit representation.

**Dependencies:** 7.8p3;10.2.1.3p8-p13/Table10.9;7.4.3.2p6;16.9.110 INT/16.9.172 REAL/16.9.53
CMPLX;7.6.1-.2;C7126/C7127;16.3/C1601.

### S7.8-006: The array constructor's dynamic type equals its declared type

**Source:** 7.8, p4; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Effect.

**Definition:** An array constructor's dynamic type is its declared type. A source expression's concrete
dynamic extension does not make a constructor polymorphic with that extension when its
declared result type is the concrete base.

**Diagnostic obligation:** not-required.

**Facets:** `limited-polymorphic-source`, `same-declared-type-different-dynamics`, `type-category-and-abstract-source-use`.

**Oracle:** Only the finite source-supported value/type/parameter observations below are planned.
Their independent literals, complete state and actual constructor consumers must be
checked before fixture authoring.

**Oracle limitation:** No runtime witness is implemented. Use independently fixed small values, named element
setup and direct constructor observations; a destination declaration or a second use of
the same operation is not an independent oracle. Source sequence order is not an
unspecified function-evaluation order. Read only defined values with established
allocation/association and valid parameter state. No C_INT, KIND-number, extra-kind,
byte-width, IEEE-layout, arbitrary-bit or processor-choice premise is assumed.

**Dependencies:** 7.8p4;C7120/C7122/C7124/C7125;7.3.2.3;11.1.11.2;15.5.2.4-.5;19.4.

### S7.8-007: Zero-trip implied-DO character lengths cannot depend on the index or nonconstant expressions

**Source:** 7.8, p5; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Restriction.

**Definition:** For a CHARACTER ac-value in an ac-implied-do with zero iteration count, its character
length cannot depend on the ac-do-variable and cannot depend on an expression that is
not a constant expression. These are independent conditions on that ac-value's length,
not a ban on every dynamic result LEN or a waived condition when an explicit constructor
type-spec is supplied.

**Diagnostic obligation:** not-required.

**Facets:** `constant-length-zero-trip-control`, `index-dependent-length-contrast`, `nonconstant-length-contrast`, `constant-expression-and-no-ac-value-boundaries`.

**Oracle:** This plain restriction has no newly mandated diagnostic. Preserve both dependency
conditions and use only valid zero/nonzero controls until an independent optional
policy/source gate exists.

**Oracle limitation:** No runtime witness is implemented. Use independently fixed small values, named element
setup and direct constructor observations; a destination declaration or a second use of
the same operation is not an independent oracle. Source sequence order is not an
unspecified function-evaluation order. Read only defined values with established
allocation/association and valid parameter state. No C_INT, KIND-number, extra-kind,
byte-width, IEEE-layout, arbitrary-bit or processor-choice premise is assumed. Do not
infer that a zero trip count makes arbitrary undefined character lengths safe.

**Dependencies:** 7.8p5;10.1.12p1(2)/(14);R783;11.1.7.4.1;19.4p5;7.4.4.2;16.9.122;4.1.2p3/4.2.

### S7.8-008: Implied DO expands by the ordinary DO initialization and execution rules

**Source:** 7.8, p6, p7; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Effect.

**Definition:** An ac-implied-do expands its body into a sequence under its ac-do-variable.
Initialization and execution follow the DO construct's rules, including typed
initial/terminal/increment parameters, default increment1, nonzero increment, variable
definition and iteration count. Scope/attributes remain the separate statement-entity
rules in19.4.

**Diagnostic obligation:** not-required.

**Facets:** `default-increment-sequence`, `positive-and-negative-strides`, `multiple-body-values`, `nested-dependent-bounds`, `array-valued-body-sequence`, `kind-and-host-scope-source-use`, `control-evaluation-and-zero-step-source-use`.

**Oracle:** Independent finite integer lists establish iteration/body/flattened order. Keep source
order of resulting elements distinct from an unprescribed total order of unrelated
function evaluations.

**Oracle limitation:** No runtime witness is implemented. Use independently fixed small values, named element
setup and direct constructor observations; a destination declaration or a second use of
the same operation is not an independent oracle. Source sequence order is not an
unspecified function-evaluation order. Read only defined values with established
allocation/association and valid parameter state. No C_INT, KIND-number, extra-kind,
byte-width, IEEE-layout, arbitrary-bit or processor-choice premise is assumed. No DO
CONCURRENT, post-scope index read, zero-step trap or compiler-produced sequence is an
oracle.

**Dependencies:** 7.8p6/p7;11.1.7.4.1/.3/.5;R1124/C1121;19.4p1-p2/p5;10.1.4p2-p3/10.1.7;19.6.5(4).

### S7.8-009: An empty constructor sequence is a zero-sized array

**Source:** 7.8, p8; J3/24-007, 18 December 2023, physical PDF 115. **Class:** Effect.

**Definition:** An empty element sequence forms a zero-sized array. The constructor remains rank one and
retains its valid specified or inferred type/parameters. Empty sequence, empty syntax
and unallocated or disassociated state are different.

**Diagnostic obligation:** not-required.

**Facets:** `typed-empty-and-zero-trip`, `zero-sized-array-ac-value`, `empty-character-parameters`, `state-and-optional-evaluation-source-use`.

**Oracle:** Observe the constructor's actual cardinality/type parameters with a nonempty positive
control. Merely allocating a zero-size destination or checking a declared rank-one
variable is not a constructor-only oracle.

**Oracle limitation:** No runtime witness is implemented. Use independently fixed small values, named element
setup and direct constructor observations; a destination declaration or a second use of
the same operation is not an independent oracle. Source sequence order is not an
unspecified function-evaluation order. Read only defined values with established
allocation/association and valid parameter state. No C_INT, KIND-number, extra-kind,
byte-width, IEEE-layout, arbitrary-bit or processor-choice premise is assumed.

**Dependencies:** 7.8p8/p1/p2/p5;R778;19.6.2;9.7.1;16.9.122 LEN/16.9.171 RANK/16.9.194 SIZE;10.1.7;19.6.6.

<!-- END GENERATED 7.8 -->

## Complete finite pending plans

All facets remain pending. Phase labels and expected values below are plans, not programs, native observations or represented coverage.

### Pending R777

* **`slash-parenthesis-admission`** - PENDING - Compile admission: a complete ordinary program uses (/ 11,13 /) in a valid INTEGER array context. Values and delimiters are known; no unrelated procedure-argument error is introduced.
* **`square-bracket-admission`** - PENDING - Compile admission: the analogous [11,13] form. A later source-use connection to an existing bracket-form witness is preferable to a renamed duplicate.
* **`mismatched-closing-delimiter`** - PENDING - Diagnostic/control: in an otherwise complete assignment to a rank-one INTEGER destination, use [11,13/) or (/11,13]; replace only the closing delimiter by its matching form. Require an array-constructor delimiter cause, not generic EOF or an outer CALL-list error.
* **`type-and-value-consumer-source-use`** - PENDING - Source-use graph: R778/R779/R780, existing R702 consumers and the separate value/flattening plans retain their owners. Delimiter admission does not prove value order or an empty-array effect.

### Pending R778

* **`typed-empty-integer`** - PENDING - Compile admission: [INTEGER ::] and (/ INTEGER :: /) in complete INTEGER array contexts. These are typed empty ac-specs, not empty expressions or scalar constructors.
* **`typed-empty-other-categories`** - PENDING - Compile admissions after their canonical context checks: fixed default CHARACTER(LEN=3), an accessible prior nonabstract derived type, a prior enum type and a prior enumeration type with no ac-values. An ordinary derived type's unsupplied components do not require scalar structure-constructor arguments when there are zero array elements.
* **`typed-nonempty`** - PENDING - Compile admission: [INTEGER :: 11,13], retaining the :: separator and C7121/p3 conditions; existing R702_valid__intrinsic remains canonical where its type-spec use suffices.
* **`untyped-nonempty`** - PENDING - Compile admission: [11,13] or a nonempty ac-value list whose expansion is empty. Inference uses the ac-value expressions' declared characteristics, not a requirement that an element be produced.
* **`untyped-empty-list`** - PENDING - Diagnostic/control: [] or (/ /) appears in a complete otherwise-valid INTEGER array assignment; insert only INTEGER ::. Do not blame this ac-spec deficiency on a different delimiter or missing procedure argument.
* **`type-spec-parameter-context-graph`** - PENDING - Source-use graph: R702, C701/C702, C726 and C795-C7100 govern allowed type parameters. A destination ALLOCATABLE attribute does not license CHARACTER(:) or a deferred PDT parameter inside this type-spec. Assumed * is not a general array-constructor length placeholder.

### Pending R779

* **`opening-bracket-source-use`** - PENDING - Source-use plan: connect the actual [ token of R777's square-bracket forms to this defining syntax owner. Do not create an empty wrapper program or repurpose a generic source-character diagnostic.

### Pending R780

* **`closing-bracket-source-use`** - PENDING - Source-use plan: preserve the defining ] token and R777's matched-pair context. Reuse a qualified square-form source connection rather than duplicate the same whole program.

### Pending R781

* **`scalar-expression-admission`** - PENDING - Compile admissions: a defined scalar INTEGER variable and a small INTEGER literal are ac-values in one homogeneous constructor. A separate [(1.0,2.0)] has one scalar COMPLEX expression, not two REAL elements or an implied DO. An ordinary runtime constructor is not required to be a constant expression.
* **`array-expression-admission`** - PENDING - Compile admission: a defined rank-two INTEGER array and a differently shaped rank-one array are ac-values of one constructor. C7120 is not a same-rank or same-shape rule for these sources.
* **`implied-do-admission`** - PENDING - Compile admission: a complete integer implied DO with a nonempty body list, scalar INTEGER controls and an established variable type.
* **`expression-category-and-state-graph`** - PENDING - Source-use graph: C7124/C7125 exclude the ac-value itself, not every component recursively. Pointer and allocatable expressions require live associated/allocated defined data when their values are used; they are not status-only or pointer-broadcast constructors.

### Pending R782

* **`single-body-value`** - PENDING - Compile admission: [(i, INTEGER :: i=1,3)] uses a single scalar body value and a complete locally typed control.
* **`multiple-body-values`** - PENDING - Compile admission: [(i,10*i, INTEGER :: i=1,2)] has two body ac-values per iteration. Their later sequence oracle is [1,10,2,20], not an elementwise sum or a rank-two result.
* **`nested-form`** - PENDING - Compile admission: [((7, INTEGER :: j=1,2), INTEGER :: i=1,2)] uses distinct nested statement entities; integer controls are not extra ac-values.
* **`missing-control-separator`** - PENDING - Diagnostic/control: omit only the comma between literal body value7 and a complete INTEGER :: i=1,2 control; restore that comma. Keep the enclosing constructor/program closed and require the implied-DO body/control separator cause.
* **`missing-body-list`** - PENDING - Diagnostic/control: keep the complete parenthesized comma/control form but omit its ac-value-list; insert literal7 before the separating comma. Zero trip count would not waive the syntactic nonempty-list requirement.

### Pending R783

* **`inferred-integer-variable`** - PENDING - Compile admission: under IMPLICIT NONE, a scalar INTEGER i is declared in the containing scope before [(i,i=1,3)]. The ac-do i is a separate statement entity; this is not an implicit host declaration.
* **`inline-default-integer`** - PENDING - Compile admission: [(i,INTEGER :: i=1,3)] needs no containing-scope declaration of i. Outside its ac-implied-do that spelling does not create a host variable.
* **`inline-supported-kind`** - PENDING - Compile admission/source-use: a named supported kind, such as KIND(0), appears in INTEGER(KIND=k) :: i. Any differentiated-kind runtime witness must independently establish supported distinct kinds; SELECTED_INT_KIND(18) need not differ from default.
* **`required-two-bounds`** - PENDING - Diagnostic/control: a complete typed control supplies initial1 but omits the terminal bound; add only ,3 before the matching implied-DO parenthesis. Do not leave an unclosed outer constructor.
* **`integer-and-scalar-bound-conditions`** - PENDING - Six diagnostic/control designs independently cover initial, terminal and explicit-increment positions: replace REAL1.0/3.0/2.0 by INTEGER1/3/2 respectively, or rank-one INTEGER [1]/[3]/[2] by the corresponding scalar. Each complete typed control has only that one type or rank fault; all other controls are defined and the repaired increment is nonzero. Require the specific control-position/type-or-rank cause, not generic kind or lookup recovery.
* **`runtime-bound-and-step-expressions`** - PENDING - Compile admission: separately defined scalar INTEGER lower=1, upper=5, stride=2 are used without PARAMETER. Constancy is needed only in a surrounding constant-expression context.
* **`loop-execution-and-zero-step-source-use`** - PENDING - Source-use graph: DO conversion, default increment1, nonzero-step restriction, count and variable definition remain11.1.7.4/p7. A scalar INTEGER zero step meets this grammar but is not a legal loop execution; do not invent a new R783 fatal diagnostic for that prose restriction.

### Pending R784

* **`bare-scalar-integer-name`** - PENDING - Compile admission: a declared scalar INTEGER name or an inline INTEGER-specified statement variable controls a complete implied DO.
* **`literal-is-not-control-variable`** - PENDING - Diagnostic/control: [(7,1=1,2)] is used in a complete context with an INTEGER i available; replace only the literal control-left-side1 by i. The body does not depend on an undeclared or invalid designator.
* **`scope-and-designator-consumer-graph`** - PENDING - Source-use graph: R1124/C1121 and19.4p1-p2/p5 own scalar/name/type and scope rules. Array elements, components, named constants, host-array name collisions and post-loop host uses need their actual canonical qualifications rather than one broad variable error.

### Pending C7120

* **`same-type-kind-different-ranks`** - PENDING - Compile admission: [11,vec,matrix] uses defined default INTEGER scalar/rank-one/rank-two sources with different shapes. A later literal sequence oracle belongs to the flattening effect, not a same-shape restriction.
* **`different-intrinsic-type`** - PENDING - Diagnostic/control: [1,2.0] has INTEGER and REAL ac-values with type-spec omitted; replace only2.0 by2. Avoid simultaneous character-length, kind-support or undefined-value defects.
* **`different-supported-intrinsic-kinds`** - PENDING - Processor-qualified diagnostic/control plan: only after two distinct supported INTEGER kinds are established, use equal small representable values of those kinds in an untyped constructor. Repair one element's kind to the other. An unavailable selector or assumed codes1/4/8 is not kind-mismatch evidence.
* **`different-derived-kind-tags`** - PENDING - Diagnostic/control matrix: one PDT has two abstract user KIND parameters a/b, fixed LEN n=1 and a scalar INTEGER payload. left has tuple(2,3); right has either(2,4) or(3,3). In [left,right], repair only the differing right declaration coordinate to(2,3); primitive payloads11/13 and LEN remain unchanged. Both KIND positions matter, and neither parameter selects an intrinsic representation.
* **`declared-dynamic-length-and-identity-source-use`** - PENDING - Source-use graph: same declared nonabstract CLASS(base) values may have different dynamic extension types; p4 still fixes the result dynamic type. Character/PDT LEN mismatch is p2, and equal values or enum ordinals do not establish same type.

### Pending C7121

* **`intrinsic-type-admissions`** - PENDING - Compile admissions: explicit INTEGER with known small INTEGER/REAL/COMPLEX values, explicit REAL with INTEGER/REAL/COMPLEX values, explicit COMPLEX with INTEGER/REAL/COMPLEX values, default CHARACTER with CHARACTER values, and LOGICAL with LOGICAL values. Conversion effects are separately planned; no blanket all-types coercion or character/logical numeric mixing is admitted.
* **`intrinsic-type-mismatch`** - PENDING - Diagnostic/control plans: [INTEGER :: .true.] repaired only to [INTEGER :: 1], and [LOGICAL :: 1] repaired only to [LOGICAL :: .true.]. Type mismatch is not kind, rank, value-range or evaluation evidence.
* **`enum-correct-primary-admission`** - PENDING - Compile admission/source-use: a prior named enum with INTEGER enumerators one=1 and two=2 supplies [enum_name :: one,one+1], using those known representable values and complete enum context. This is not an ENUMERATION TYPE or an arbitrary raw INTEGER conversion.
* **`enum-wrong-integer-provenance`** - PENDING - Diagnostic/control: [enum_name :: 1] has a known-representable INTEGER value but lacks a primary from that enum; replace only1 by its enumerator one. A second small-value contrast replaces an INTEGER enumerator from another enum definition by one. Keep enum range and accessibility valid.
* **`boz-conjunction-and-char-kind-graph`** - PENDING - Source-use graph: C7119/C7126 restrict BOZ array values to explicit INTEGER/REAL even though this rule mentions BOZ. Other CHARACTER-kind compatibility and representability conditions remain p3/10.2.1.2, not a new C7121 type-only waiver.

### Pending C7122

* **`same-derived-type-admission`** - PENDING - Compile admission/source-use: a prior ordinary nonabstract record with defined scalar payloads11/13 supplies [record :: left,right]. Preserve R702_valid__derived and its actual role instead of copying its program.
* **`different-declared-type`** - PENDING - Diagnostic/control: a typed [base :: other_value] uses a distinct ordinary nonabstract declared type whose primitive fields are defined; replace only other_value by a separately defined base_value. Do not rely on matching layout or a derived assignment conversion.
* **`different-user-kind-parameter`** - PENDING - Diagnostic/control matrix: one PDT has user KIND parameters a/b, LEN n and scalar INTEGER payload. A type-spec t(a=2,b=3,n=1) and left with that tuple are paired with right(a=2,b=4,n=1) or right(a=3,b=3,n=1). Repair only the differing right declaration coordinate; keep payload11/13 and LEN fixed. No INTEGER(a) or other intrinsic representation selector is used.
* **`declared-not-dynamic-and-len-graph`** - PENDING - Source-use graph: a defined CLASS(base) expression with child dynamic type has declared base type and can meet this constraint when base is concrete; TYPE(child) is not the same declared type. Equal KIND with different fixed LEN meets this constraint but still needs p3 compatibility; do not credit a LEN complaint as C7122.

### Pending C7123

* **`same-enumeration-admission`** - PENDING - Compile admission/source-use: a prior enumeration type supplies scalar constants, a defined same-type array and an implied-DO body constant of that type. INTEGER loop controls are not ac-values. Preserve R702_valid__enumeration where its claim matches.
* **`integer-is-not-enumeration`** - PENDING - Diagnostic/control: [direction :: 1] is repaired by replacing only1 by direction's first enumerator. The raw INTEGER is not an implicit enumeration constructor; an INTEGER ENUM enumerator has the same category problem.
* **`other-enumeration-type`** - PENDING - Diagnostic/control: two distinct named enumeration types have first enumerators of ordinal1; replace only the wrong type's ac-value by the correct type's first value. Keep both complete definitions and avoid a raw INTEGER repair.
* **`identity-and-constructor-source-use`** - PENDING - Source-use graph:7.6.2/R770/R771/C7116, prior-definition and scalar INTEGER constructor-range conditions retain their owners. Do not infer a KIND parameter or C interoperability for these values.

### Pending C7124

* **`limited-value-admissions`** - PENDING - Compile admissions: defined intrinsic values and declared concrete TYPE(base) or CLASS(base) values in otherwise conforming constructors; no CLASS(*) expression is supplied.
* **`unlimited-value-focused-contrast`** - PENDING - Diagnostic/control design: a complete module procedure has CLASS(*),IN scalar x and SELECT TYPE(typed=>x), TYPE IS(INTEGER), reached with a defined INTEGER actual. In that branch pass the one-ac-value untyped [x] to a separate explicit CLASS(*),IN rank-one observer; repair only x inside the constructor to typed. The original dummy stays unlimited, the refined associate is INTEGER, and neither an explicit type-spec nor a fixed-type receiver adds a separate conformance defect. Require the unlimited-polymorphic ac-value cause, not vague inability to infer a type.
* **`outer-value-versus-component-source-use`** - PENDING - Source-use gate: a TYPE(record) value is not CLASS(*) merely because a component is polymorphic. Any such component/allocated-state witness needs its actual7.5.10/assignment/lifetime qualifications; no unallocated payload or empty classifier is proposed.

### Pending C7125

* **`declared-abstract-contrast`** - PENDING - Diagnostic/control design: an ordinary ABSTRACT base has scalar INTEGER payload and no deferred bindings; a concrete child actual with named payload11 reaches a CLASS(base),IN scalar dummy. Pass the untyped [arg] to a legal CLASS(base),IN rank-one observer. Remove only ABSTRACT and its comma from base. No TYPE(base) object/dummy or explicit [base ::] introduces C706/C703.
* **`concrete-child-admission`** - PENDING - Compile admission: a TYPE(child) value from an ordinary concrete extension of that abstract base is initialized through its primitive inherited payload and used as an ac-value. No whole abstract-parent designator is read.
* **`type-spec-and-temporary-source-use`** - PENDING - Source-use graph: C703, C706, C7101 and abstract allocation rules retain their owners. A compiler-created illegal temporary or ASR verifier complaint is not an adequate C7125 source diagnostic.

### Pending C7126

* **`typed-integer-boz-admission`** - PENDING - Compile admission plan: a short valid BOZ literal such as B'1' appears in [INTEGER :: B'1'] with complete source context. This is syntax/type admission, not proof of an arithmetic or native representation result.
* **`typed-real-qualified-admission`** - PENDING - Processor-qualified compile admission: use an explicitly supported REAL kind and a separately established valid real representation, respecting C7127 and any padding/truncation. No universal all-zero/IEEE bit pattern is invented.
* **`omitted-type-spec`** - PENDING - Diagnostic/control: a valid short BOZ token occurs as the sole ac-value without type-spec; insert only INTEGER ::. The C7119 global context condition overlaps this same missing typed INTEGER/REAL context and retains its own definition, not a separate source corruption.
* **`wrong-type-spec`** - PENDING - Diagnostic/control: pass [LOGICAL :: B'1'] to an explicit CLASS(*),INTENT(IN) rank-one observer so the surrounding consumer accepts either type; change only LOGICAL to INTEGER. Do not use a fixed LOGICAL destination that would invalidate the INTEGER repair. CHARACTER/enum alternatives need complete prior type contexts and the same consumer-neutral INTEGER repair, not an unqualified REAL pattern.
* **`nested-boz-and-allowed-use-source-use`** - PENDING - Source-use graph: the same requirement applies inside an ac-implied-do; its INTEGER controls and all consumer conditions remain. An intrinsic INT(BOZ) result is an INTEGER expression, a different form from a direct BOZ ac-value. Unapproved sourcec0c9e5de is not fixture or REAL-representation authority.

### Pending C7127

* **`valid-pattern-documentary-gate`** - PENDING - Processor-qualified admission plan: bind the actual supported REAL kind, storage size and representation documentation, then one valid BOZ pattern and its applicable padding/truncation. A normal numeric REAL literal is not a representation proof.
* **`invalid-pattern-diagnostic-gate`** - PENDING - Conditional diagnostic/control plan only after such evidence exists: in a complete typed REAL array constructor, choose a proven invalid pattern and repair only that literal to a proven valid same-kind pattern. Keep lexical digits, kind support and C1601 valid. A processor need not provide a universally usable invalid encoding, so no invented NaN/infinity trap or placeholder negative is authorized.
* **`real-boz-and-truncation-owner-graph`** - PENDING - Source-use gate: preserve S10_2_1_3_017_valid__real and its ieee-binary profile in needs-oracle state. Arithmetic/radix/precision checks do not establish bit-to-value layout. Nonzero discarded bits under REAL conversion are C1601, not proof of C7127 invalid representation; no profile or receipt is changed here.

### Pending C7128

* **`nested-same-name`** - PENDING - Diagnostic/control: [((7,INTEGER :: i=1,2),INTEGER :: i=1,2)] has a constant body and repeated nested control name. Change only the inner control-left-side i to j; no body reference needs repair and both loops remain otherwise valid. Require nested ac-do-variable reuse, with19.4's statement-entity scope also preserved.
* **`distinct-nested-variables`** - PENDING - Compile admission: the repaired inner j/outer i form. Inline types establish both INTEGER statement entities and do not declare containing-scope variables.
* **`disjoint-reuse-admission`** - PENDING - Compile admission/source-use: two nonnested implied DOs use i in their separate scopes with bounds1:2 and3:4. A future value witness independently expects[1,2,3,4]; the nested prohibition must not reject this disjoint reuse.

### Pending S7.8-001

* **`rank-one-and-scalar-sequence`** - PENDING - Runtime plan: direct observations of [11,13,17] establish rank1, size3 and those three indexed values. Do not infer result rank solely from an independently rank-one destination declaration.
* **`higher-rank-flattening`** - PENDING - Runtime plan: set m(1,1)=11,m(2,1)=13,m(1,2)=17,m(2,2)=19 by names, then directly inspect [5,m,23] as the rank-one sequence[5,11,13,17,19,23]. No RESHAPE or constructor supplies the expected ordering or matrix setup.
* **`mixed-shapes-and-empty-source`** - PENDING - Runtime plan: defined rank-one sources of lengths1 and3 plus an actual defined zero-size array contribute concatenated values and no elements for the empty source. Check exact size and indexed markers; neither equal source shapes nor scalar broadcast is required.
* **`value-expression-state-source-use`** - PENDING - Source-use plan: a live associated pointer or allocated allocatable array ac-value contributes its defined data values, not its association/allocation status. Before any new witness, establish complete state and parameters; a pointer-containing derived element retains its scalar-constructor/assignment owners and no pointer broadcasting is inferred.
* **`evaluation-order-and-shared-consumer-graph`** - PENDING - Source-use graph:10.1.4/10.1.7 retain control-expression evaluation, side-effect restrictions and optional operand evaluation. Do not use mutable callback order or absence as the flattening oracle. Existing R702/S10 witnesses retain their primaries; a future direct sequence witness is not a renamed assignment program.

### Pending S7.8-002

* **`character-length-source-contrast`** - PENDING - Optional-policy/source-contrast plan: in a complete untyped ['A','BC'] context, repair only 'A' to 'A ' so lengths agree while type/kind remain default CHARACTER. No diagnostic is newly mandated; no invalid result length or trap is observed.
* **`derived-len-source-contrast`** - PENDING - Optional-policy/source-contrast matrix: one PDT has fixed common user KIND2, two LEN parameters n/m and a scalar INTEGER payload independent of n/m. left has LEN tuple(1,2); right differs in only n or only m. Repair only that declaration coordinate to(1,2). Both payloads are initialized by names; no kind, declared-type, component-shape or representation mismatch supplies the cause.
* **`runtime-equal-length-controls`** - PENDING - Runtime positive controls: two separately defined default CHARACTER values of equal length2 form ['AB','CD']-valued results observed with assumed-length character arguments. A deferred-length allocated variant needs successful allocation, defined payloads and equal established lengths before construction.
* **`zero-size-and-explicit-spec-boundaries`** - PENDING - Source-use graph: zero produced elements do not turn syntactically present ac-values into no type/length constraints. Explicit CHARACTER length changes the p2 antecedent and permits qualified conversion, while p5 independently restricts character lengths in zero-trip implied DOs.

### Pending S7.8-003

* **`inferred-integer-kind`** - PENDING - Runtime plan: one supported INTEGER kind obtained symbolically is used by every ac-value, and KIND of the constructor expression is checked against that selector. Values11/13 are independently checked; the expected KIND is not a numeric identifier.
* **`inferred-character-length`** - PENDING - Runtime plan: two defined default CHARACTER(2) sources AB/CD produce a length2, size2 constructor observed directly. Do not assign first to a fixed CHARACTER(2) receiver and treat that declaration's LEN as evidence.
* **`explicit-type-and-runtime-length`** - PENDING - Runtime plan: a defined scalar INTEGER n=3 supplies [CHARACTER(LEN=n) :: 'A','BC']; direct observation checks length3 and values 'A  '/'BC '. LEN need not be constant in this ordinary executable context; surrounding constant-expression requirements remain separate.
* **`nonintrinsic-identity-consumer-source-use`** - PENDING - Source-use graph: prior concrete derived, named enum and enumeration type specifiers retain R702/R703/C795/C7112/C7116 and their exact identities. Existing typed-array cases are preserved without generic KIND-of-enum or same-type-from-equal-values shortcuts.
* **`deferred-assumed-and-destination-boundary`** - PENDING - Source-use graph: C702 and C726/C7100 control colon/asterisk contexts. An ALLOCATABLE destination cannot license a deferred type-spec inside the array constructor. Pointer/allocatable source entities have established values/parameters; the resulting expression is not an allocatable or pointer variable by inheritance.

### Pending S7.8-004

* **`fixed-derived-len-compatibility`** - PENDING - Optional-policy/source-contrast plan: after satisfying C7122's identical derived type/KIND, use a differently fixed LEN value and repair only the source object's LEN declaration. Do not attribute a LEN failure to C7122 or borrow allocatable-destination reallocation for a constructor type-spec.
* **`character-kind-domain-qualification`** - PENDING - Processor-qualified plan: independently establish actual character-kind support and the exact10.2.1.2 default/ASCII/ISO10646 versus other-kind conditions before testing different kinds. Source code acceptance and a selected-kind number do not prove repertoire, representation or conversion.
* **`defined-assignment-is-not-coercion`** - PENDING - Source-use/optional-policy plan: an available INTEGER-to-record defined assignment does not make an INTEGER ac-value conform to a typed derived array constructor. A future complete contrast must retain the valid binding and replace only the value by an independently defined same-type record; canonical numbered type conditions retain ownership.
* **`shape-pointer-and-consumer-boundaries`** - PENDING - Source-use graph: scalar and array ac-values are flattened/contributed under p6, not required to have one common input shape. Pointer/allocatable and component assignment conditions remain canonical; ordinary assignment scalar expansion does not broadcast a data pointer into a pointer component.

### Pending S7.8-005

* **`small-numeric-conversion`** - PENDING - Processor-qualified runtime matrix: after independently establishing the needed numeric literal/conversion accuracy, use nominal REAL inputs4.0/-3.0 for INTEGER expectations[4,-3,2] in [INTEGER :: source,2], INTEGER-2/4 for REAL expectations-2.0/4.0, and INTEGER2/REAL4.0/COMPLEX(5.0,-3.0) for COMPLEX expectations(2.0,0.0)/(4.0,0.0)/(5.0,-3.0). These exact real/complex comparisons are not universal merely because inputs are small. REAL/CMPLX approximation clauses and default-REAL recommendations retain their qualifications; never obtain the sole oracle by applying INT/REAL/CMPLX to the same inputs.
* **`character-padding-and-truncation`** - PENDING - Runtime plan: [CHARACTER(LEN=3) :: 'A','BCDE'] has independent expected 'A  '/'BCD'. An assumed-length observer checks both LEN and named element values before any differently typed destination could mask conversion.
* **`nonzero-dependent-character-length`** - PENDING - Runtime plan: with a defined CHARACTER(3) PARAMETER text='ABC', a nonzero i=1:3 implied DO contributes text(1:i) under explicit CHARACTER(LEN=3); expected elements are 'A  ','AB ','ABC'. No substring is out of range. This is not the zero-trip p5 case.
* **`enum-conversion-source-use`** - PENDING - Source-use graph: an explicit enum type can convert only qualifying INTEGER expressions with a correct enum primary, with representable values; INT of an enum and INT of an enumeration have different meanings. Preserve S10_2_1_3_022_valid and R702 enum/enumERATION contexts without cloned executions.
* **`boz-conversion-and-representation-gate`** - PENDING - Source-use/profile gate: C7119/C7126 allowance, C7127 REAL representation, C1601 discarded bits and16.3/INT/REAL conversion are all required. Keep arithmetic expected values independently justified; no REAL IEEE pattern or arbitrary signed/oversized bit sequence is inferred from compiler agreement.

### Pending S7.8-006

* **`limited-polymorphic-source`** - PENDING - Runtime plan: a live defined TYPE(child) actual reaches a CLASS(base),IN scalar dummy for an ordinary nonabstract base. Form the untyped [arg] and pass it to a separate CLASS(base),IN rank-one observer; TYPE IS(base) must select and payload11 must be observed. No SELECT TYPE on a nonpolymorphic selector or TYPE(abstract) object is used.
* **`same-declared-type-different-dynamics`** - PENDING - Runtime plan: two defined CLASS(base) scalar dummies with distinct concrete extension dynamic types but identical declared type/KIND supply one constructor. Direct polymorphic-array observation selects base and independently checks payloads11/13; do not use dynamic-type equality as the C7120 premise.
* **`type-category-and-abstract-source-use`** - PENDING - Source-use graph: C7124/C7125 still forbid unlimited-polymorphic or declared-abstract ac-values. Explicit C7122 tests declared type, not extension compatibility; type guards and argument association retain11.1.11/15.5/19.4 ownership.

### Pending S7.8-007

* **`constant-length-zero-trip-control`** - PENDING - Runtime positive-control plan: a constant CHARACTER value 'AB' in a literal1:0 implied DO has empty contribution with known length2. A typed CHARACTER(LEN=3) form may convert the result type but still uses a constant-length source; directly check size0 and its constructor LEN.
* **`index-dependent-length-contrast`** - PENDING - Optional-policy/source contrast only: with CHARACTER(2) PARAMETER text='AB', the zero-trip [CHARACTER(LEN=2) :: (text(1:i),INTEGER :: i=1,0)] has index-dependent ac-value length. Repair only the substring upper bound to1. Do not execute the invalid case or count generic undefined/inference recovery as this cause.
* **`nonconstant-length-contrast`** - PENDING - Optional-policy/source contrast only: a separately declared, defined INTEGER variable n=1 controls text(1:n) inside an unrelated zero-trip j loop. Repair by making n a PARAMETER, without changing its value, source kind or loop. Constancy is a source property, not a compiler-folded-value observation.
* **`constant-expression-and-no-ac-value-boundaries`** - PENDING - Source-use qualification: an ac-do-variable can be a constant-expression primary under10.1.12 while the separate p5 index-dependence prohibition still applies. A nonzero typed loop permits qualified varying source lengths. [CHARACTER(LEN=n) ::] with defined n=3 has no ac-value, so p5's ac-value antecedent is absent; do not ban that typed-empty runtime LEN by analogy.

### Pending S7.8-008

* **`default-increment-sequence`** - PENDING - Runtime plan: [(i,INTEGER :: i=1,3)] produces the independent sequence[1,2,3], with no host final-index assertion.
* **`positive-and-negative-strides`** - PENDING - Runtime plan: bounds1,5,2 produce[1,3,5]; bounds5,1,-2 produce[5,3,1]. Small values and increments avoid overflow; a second execution of the same implied DO is not the expected oracle.
* **`multiple-body-values`** - PENDING - Runtime plan: body values i and10*i over1:2 produce[1,10,2,20], checking per-iteration body placement rather than grouping all first values before second values.
* **`nested-dependent-bounds`** - PENDING - Runtime plan: distinct outer i=1:3 and inner j=1:i produce10*i+j values[11,21,22,31,32,33]. The inner bound reads an already defined outer statement entity, never its own not-yet-defined control variable. All outer iterations are nonzero in this finite plan.
* **`array-valued-body-sequence`** - PENDING - Runtime plan: define vector entries31/37 by names, then body vector+i over i=1:2 contributes[32,38,33,39] in order. This remains a rank-one result, not a rank-two block or an elemental structure constructor.
* **`kind-and-host-scope-source-use`** - PENDING - Source-use graph:19.4 says the index is a scalar INTEGER statement entity with specified or inferred type/parameters and no other attributes. A future host i=99 witness checks that host value separately remains99; an inline INTEGER control does not declare a host name. Kind differentiation needs actually supported distinct selectors, not assumed codes.
* **`control-evaluation-and-zero-step-source-use`** - PENDING - Source-use graph:10.1.4p3 requires control-expression evaluation, while10.1.4p2/10.1.7 constrain side effects/optional operand evaluation. Use defined literal or separate named bounds in ordinary witnesses; nested-zero/side-effect counts and self-referential limits are not inferred. Zero step is the canonical DO prose restriction, not a new R783/C7128 diagnostic policy.

### Pending S7.8-009

* **`typed-empty-and-zero-trip`** - PENDING - Runtime plan: directly inspect [INTEGER ::] and [(i,INTEGER :: i=1,0)] for size0 and rank1, with a nonempty [7] control of size1/rank1/value7. The latter has a nonempty ac-value-list whose expansion is empty; untyped[] remains a syntax error.
* **`zero-sized-array-ac-value`** - PENDING - Runtime plan: a defined ordinary INTEGER empty(0) contributes no values in [11,empty,13]; check size2 and exact[11,13]. Use an actually allocated zero-size source only after status is established; do not substitute an unallocated object.
* **`empty-character-parameters`** - PENDING - Runtime plan: direct observation of typed-empty CHARACTER(LEN=3) has size0 and LEN3. A separately defined runtime n=3 in [CHARACTER(LEN=n) ::] is a distinct valid no-ac-value context; a zero-trip CHARACTER ac-value still needs p5's conditions.
* **`state-and-optional-evaluation-source-use`** - PENDING - Source-use graph:19.6.2's always-defined zero-size values do not permit reading absent allocation data or deferred lengths. SIZE/LEN have their actual argument conditions. Preserve10.1.7/19.6.6 undefined-status consequences rather than using a side-effect counter to assert that an unneeded operand was never evaluated.

## Canonical cases and integration boundary

All1907 base execution IDs, input bytes and fingerprints remain protected. There are no existing primary R777-R784/C7120-C7128 cases at this base. Existing type/declaration, assignment, conversion and BOZ witnesses are not renamed, weakened or granted new local facet credit.

* `R605_valid__boz` - primary `R605`, `positive-control`, `tests/clause06/R605_valid__boz.f90`.
* `R702_valid__derived` - primary `R702`, `positive-control`, `tests/clause07/R702_valid__derived.f90`.
* `R702_valid__enum` - primary `R702`, `positive-control`, `tests/clause07/R702_valid__enum.f90`.
* `R702_valid__enumeration` - primary `R702`, `positive-control`, `tests/clause07/R702_valid__enumeration.f90`.
* `R702_valid__intrinsic` - primary `R702`, `positive-control`, `tests/clause07/R702_valid__intrinsic.f90`.
* `R703_valid__class_derived` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__class_derived.f90`.
* `R703_valid__class_unlimited` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__class_unlimited.f90`.
* `R703_valid__classof` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__classof.f90`.
* `R703_valid__intrinsic` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__intrinsic.f90`.
* `R703_valid__type_assumed` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__type_assumed.f90`.
* `R703_valid__type_derived` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__type_derived.f90`.
* `R703_valid__type_enum` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__type_enum.f90`.
* `R703_valid__type_enumeration` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__type_enumeration.f90`.
* `R703_valid__type_intrinsic` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__type_intrinsic.f90`.
* `R703_valid__typeof` - primary `R703`, `positive-control`, `tests/clause07/R703_valid__typeof.f90`.
* `S10_2_1_3_009_valid` - primary `S10.2.1.3-009`, `effect`, `tests/clause10/S10_2_1_3_009_valid.f90`.
* `S10_2_1_3_010_valid` - primary `S10.2.1.3-010`, `effect`, `tests/clause10/S10_2_1_3_010_valid.f90`.
* `S10_2_1_3_011_valid` - primary `S10.2.1.3-011`, `effect`, `tests/clause10/S10_2_1_3_011_valid.f90`.
* `S10_2_1_3_022_valid` - primary `S10.2.1.3-022`, `effect`, `tests/clause10/S10_2_1_3_022_valid.f90`.
* `S6_2_1_001_valid__boz` - primary `S6.2.1-001`, `positive-control`, `tests/clause06/S6_2_1_001_valid__boz.f90`.
* `S6_3_2_2_001_invalid__boz:line7` - primary `S6.3.2.2-001`, `effect`, `tests/clause06/S6_3_2_2_001_invalid__boz.f90`.
* `S6_3_2_2_001_valid__boz_repair` - primary `S6.3.2.2-001`, `positive-control`, `tests/clause06/S6_3_2_2_001_valid__boz_repair.f90`.
* `S10_2_1_3_017_valid` - primary `S10.2.1.3-017`, `effect`, `tests/clause10/S10_2_1_3_017_valid.f90`.
* `S10_2_1_3_017_valid__real` - primary `S10.2.1.3-017`, `effect`, `tests/clause10/S10_2_1_3_017_valid__real.f90`.
* `S10_2_1_3_012_valid` - primary `S10.2.1.3-012`, `effect`, `tests/clause10/S10_2_1_3_012_valid.f90`.
* `S10_2_1_3_013_valid` - primary `S10.2.1.3-013`, `effect`, `tests/clause10/S10_2_1_3_013_valid.f90`.
* `S10_2_1_3_014_valid` - primary `S10.2.1.3-014`, `effect`, `tests/clause10/S10_2_1_3_014_valid.f90`.
* `S10_2_1_3_014_valid__kinds` - primary `S10.2.1.3-014`, `effect`, `tests/clause10/S10_2_1_3_014_valid__kinds.f90`.
* `S10_2_1_3_015_valid` - primary `S10.2.1.3-015`, `effect`, `tests/clause10/S10_2_1_3_015_valid.f90`.
* `S10_2_1_3_015_valid__precision` - primary `S10.2.1.3-015`, `effect`, `tests/clause10/S10_2_1_3_015_valid__precision.f90`.
* `S10_2_1_3_016_valid` - primary `S10.2.1.3-016`, `effect`, `tests/clause10/S10_2_1_3_016_valid.f90`.
* `S10_2_1_3_019_valid` - primary `S10.2.1.3-019`, `effect`, `tests/clause10/S10_2_1_3_019_valid.f90`.
* `S10_2_1_3_020_valid` - primary `S10.2.1.3-020`, `effect`, `tests/clause10/S10_2_1_3_020_valid.f90`.

`S10_2_1_3_017_valid__real` remains needs-oracle with its existing ieee-binary profile. Its arithmetic-model check is not a REAL(BOZ) representation proof. The exact1907-case/nine-link and observational-inventory comparison is recorded in `array-constructors-source-handoff.json`; no stale receipt is renewed here.

## Validation and stop point

Only pinned-source/hash/boundary, schema, reciprocal accounting, append-only ownership, complete pending-plan and render/binding checks are performed. `Registry.render(write=True)` generates the owned definitions; check-only rendering verifies them afterward. This is not a fixture test, executable model, whole-standard audit or approval. Only this catalogue and view are committed; the local index overlay is excluded. Independent source review precedes fixtures.
