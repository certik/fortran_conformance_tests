# Fortran 2023: 9.6 Image selectors

Source-only draft catalogue: `doc/catalogues/image_selectors_9_6.json`.
No Fortran test program, compiler invocation, execution, oracle approval, fixture approval, or coverage claim is supplied.

Authority: original J3/24-007, 18 December 2023, 688 pages, SHA-256 `7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.

Fifteen base units: p1, R926-R928, C932-C935, p2-p7, and the unnumbered note. Fine units record grammar components, selector-spec constraints, image-index/team/STAT/NOTIFY semantics, and the informative example.

All facets in this packet are pending source plans. Multi-image execution, teams, NOTIFY variables, and failed-image observations are separate gated capabilities.

<!-- BEGIN GENERATED 9.6 -->

### S9.6-001: Image selectors determine image indices for coindexed objects

**Source:** 9.6 p1, J3/24-007, 18 December 2023, physical PDF158. **Class:** Effect.

**Definition:** An image selector is the syntactic selector that determines the image index for a
coindexed object. The bracket form, cosubscript scalar integer syntax, optional
selector-spec list, team selection, cobound validity, and STAT/NOTIFY effects are
specified by the more specific 9.6 requirements and by the data-ref/part-ref owners that
admit image selectors on coarrays.

**Diagnostic obligation:** not-required.

**Facets:** `selector-for-coindexed-object`, `image-index-determined`, `not-array-subscript-syntax`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Numbered syntax rules and constraints carry the 4.2 detection/reporting duty; unnumbered
prose restrictions here are not promoted to mandatory static diagnostics. Multi-image
execution, failed-image detection, teams, NOTIFY variables, and cross-team coarray
establishment remain separately gated capabilities.

**Dependencies:** 4.2;5.3.4;8.5.6.1;9.4.2R912/C914-C916;9.4.3C921;9.6R926-R928/C932-C935/p2-p7.

### R926: An image selector is a bracketed cosubscript list with an optional selector-spec list

**Source:** 9.6 R926, J3/24-007, 18 December 2023, physical PDF159. **Class:** Syntax.

**Definition:** The grammar for image-selector is exactly lbracket cosubscript-list optionally followed
by a comma and an image-selector-spec-list, then rbracket. The cosubscript-list is
required and precedes any selector specs. Parentheses are array/substring syntax, not
R926 image-selector delimiters.

**Diagnostic obligation:** required.

**Facets:** `bracket-delimited-selector`, `cosubscript-list-required`, `optional-spec-list-after-comma`, `right-bracket-closes-selector`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Numbered syntax rules and constraints carry the 4.2 detection/reporting duty; unnumbered
prose restrictions here are not promoted to mandatory static diagnostics. Multi-image
execution, failed-image detection, teams, NOTIFY variables, and cross-team coarray
establishment remain separately gated capabilities.

**Dependencies:** 4.1.3;4.2;9.4.2R912/C914-C916;9.4.3C921;9.6R927-R928/C932-C935.

### R927: A cosubscript is a scalar integer expression

**Source:** 9.6 R927, J3/24-007, 18 December 2023, physical PDF159. **Class:** Syntax.

**Definition:** The grammar for cosubscript is scalar-int-expr. R927 owns the scalar integer expression
requirement; p2 owns cobound validity and image-index calculation, while C914 owns the
number of cosubscripts relative to the selected coarray's corank.

**Diagnostic obligation:** required.

**Facets:** `literal-scalar-integer-cosubscript`, `variable-scalar-integer-cosubscript`, `noninteger-or-nonscalar-cosubscript-rejected`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Numbered syntax rules and constraints carry the 4.2 detection/reporting duty; unnumbered
prose restrictions here are not promoted to mandatory static diagnostics. Multi-image
execution, failed-image detection, teams, NOTIFY variables, and cross-team coarray
establishment remain separately gated capabilities.

**Dependencies:** 4.1.3;4.2;7.4.1 integer type;10.1 expressions;9.4.2C914;9.6p2.

### R928: An image selector spec is NOTIFY, STAT, TEAM, or TEAM_NUMBER

**Source:** 9.6 R928, J3/24-007, 18 December 2023, physical PDF159. **Class:** Syntax.

**Definition:** The grammar for image-selector-spec admits exactly one of four keyword forms:
NOTIFY=notify-variable, STAT=stat-variable, TEAM=team-value, or
TEAM_NUMBER=scalar-int-expr. R928 admits the forms; C932 prohibits repeated specifiers,
C934 prohibits TEAM and TEAM_NUMBER in the same selector-spec list, C933 restricts
NOTIFY placement, and p3/p6/p7 specify the team and STAT effects.

**Diagnostic obligation:** required.

**Facets:** `notify-selector-spec`, `stat-selector-spec`, `team-selector-spec`, `team-number-selector-spec`, `stat-with-team-spec-list`, `stat-with-team-number-spec-list`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Numbered syntax rules and constraints carry the 4.2 detection/reporting duty; unnumbered
prose restrictions here are not promoted to mandatory static diagnostics. Multi-image
execution, failed-image detection, teams, NOTIFY variables, and cross-team coarray
establishment remain separately gated capabilities.

**Dependencies:** 4.1.3;4.2;9.6C932-C935/p3-p7;9.7R946 stat-variable;11.1.5.1R1115/C1115
team-value;11.6R1167/C1177-C1178 notify-variable;16.10.2.34 TEAM_TYPE.

### C932: No image selector specifier appears more than once in a selector-spec list

**Source:** 9.6 C932, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** Within a given image-selector-spec-list, no specifier keyword shall appear more than
once. Distinct specifiers may appear together subject to the independent C933 NOTIFY
placement rule, C934 TEAM/TEAM_NUMBER mutual exclusion, C935 STAT variable rule, and the
prose team/STAT requirements.

**Diagnostic obligation:** required.

**Facets:** `single-occurrence-specifiers`, `distinct-specifiers-may-coexist`, `duplicate-specifier-rejected`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Numbered syntax rules and constraints carry the 4.2 detection/reporting duty; unnumbered
prose restrictions here are not promoted to mandatory static diagnostics. Multi-image
execution, failed-image detection, teams, NOTIFY variables, and cross-team coarray
establishment remain separately gated capabilities.

**Dependencies:** 4.2;9.6R926-R928/C933-C935/p3-p7.

### C933: NOTIFY may appear only in the designator of an intrinsic-assignment variable

**Source:** 9.6 C933, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** A NOTIFY= image-selector-spec shall appear only in the designator of the variable of an
intrinsic assignment statement. It is not permitted in a mere reference, procedure
argument, defined assignment, or other context that is not the variable designator of
intrinsic assignment.

**Diagnostic obligation:** required.

**Facets:** `notify-in-intrinsic-assignment-variable`, `notify-outside-assignment-variable-rejected`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Numbered syntax rules and constraints carry the 4.2 detection/reporting duty; unnumbered
prose restrictions here are not promoted to mandatory static diagnostics. Multi-image
execution, failed-image detection, teams, NOTIFY variables, and cross-team coarray
establishment remain separately gated capabilities.

**Dependencies:** 4.2;10.2 intrinsic assignment;9.6R928/p4;11.6R1167/C1177-C1178 notify-variable.

### C934: TEAM and TEAM_NUMBER are mutually exclusive in an image selector spec list

**Source:** 9.6 C934, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** TEAM and TEAM_NUMBER shall not both appear in the same image-selector-spec-list. Either
may appear with other nonduplicated specifiers such as STAT, subject to C932, C933,
C935, and the p3 team-validity requirements.

**Diagnostic obligation:** required.

**Facets:** `team-without-team-number`, `team-number-without-team`, `team-and-team-number-together-rejected`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Numbered syntax rules and constraints carry the 4.2 detection/reporting duty; unnumbered
prose restrictions here are not promoted to mandatory static diagnostics. Multi-image
execution, failed-image detection, teams, NOTIFY variables, and cross-team coarray
establishment remain separately gated capabilities.

**Dependencies:** 4.2;9.6R928/C932/p3;11.1.5.1R1115/C1115;16.10.2.34.

### C935: A STAT variable in an image selector is not coindexed

**Source:** 9.6 C935, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** A stat-variable appearing in an image selector shall not be a coindexed object. The
stat-variable grammar and scalar integer variable form are owned by R946; this
constraint adds the image-selector-specific exclusion of coindexed STAT targets.

**Diagnostic obligation:** required.

**Facets:** `local-stat-variable`, `coindexed-stat-variable-rejected`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Numbered syntax rules and constraints carry the 4.2 detection/reporting duty; unnumbered
prose restrictions here are not promoted to mandatory static diagnostics. Multi-image
execution, failed-image detection, teams, NOTIFY variables, and cross-team coarray
establishment remain separately gated capabilities.

**Dependencies:** 4.2;9.4.3;9.6R928/p6-p7;9.7R946 stat-variable.

### S9.6-002: Cosubscript values are within cobounds and determine image index by coarray subscript order

**Source:** 9.6 p2, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** For an image selector, each cosubscript value shall be within the cobounds for its
codimension. Taking account of those cobounds, the cosubscript list determines the image
index in the same way that an array-element subscript list determines a subscript order
value in 9.5.3.3. The separate statement that the number of cosubscripts equals the
object's corank is recorded here as dependent on the registered C914 owner.

**Diagnostic obligation:** not-required.

**Facets:** `cosubscript-within-cobounds`, `single-codimension-image-index`, `multiple-codimension-subscript-order-index`, `out-of-cobounds-cosubscript-invalid`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Numbered syntax rules and constraints carry the 4.2 detection/reporting duty; unnumbered
prose restrictions here are not promoted to mandatory static diagnostics. Multi-image
execution, failed-image detection, teams, NOTIFY variables, and cross-team coarray
establishment remain separately gated capabilities. The p2/corank equality is
deliberately not duplicated from C914.

**Dependencies:** 4.2;5.3.4;8.5.6.1;8.5.6.3;9.4.2C914;9.5.3.3 table9.1;9.6R927;16.9 image inquiry
intrinsics.

### S9.6-003: TEAM selects the current or an ancestor team and requires establishment in that team

**Source:** 9.6 p3, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** If a TEAM= specifier appears in an image selector, the team of the image selector is
specified by team-value. That team-value shall identify the current team or an ancestor
team, and the selected object shall be an established coarray in that team. The
TEAM_TYPE value and CHANGE TEAM/FORM TEAM mechanisms that create valid team values are
dependencies.

**Diagnostic obligation:** not-required.

**Facets:** `team-current-team`, `team-ancestor-team`, `team-value-not-current-or-ancestor-invalid`, `object-not-established-in-team-invalid`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
TEAM= validity is runtime/source-valued unless a future case uses a statically
established team context; no mandatory static diagnostic is claimed for invalid team
identity or establishment. Multi-image execution and team construction are separate
gated suite capabilities.

**Dependencies:** 4.2;5.3.4;8.5.6.1;9.6R928/C934;11.1.5.1R1115/C1115;11.1.5.2;11.7.9;16.10.2.34
TEAM_TYPE;19.5.1.6 established coarrays.

### S9.6-004: TEAM_NUMBER outside the initial team selects a sibling team and requires parent or associating establishment

**Source:** 9.6 p3, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** If TEAM_NUMBER= appears and the current team is not the initial team, the scalar integer
value shall equal a team number for a sibling team of the current team, and the image
selector's team is that sibling team. The object shall be an established coarray in the
parent of the current team, or an associating entity of the CHANGE TEAM construct.

**Diagnostic obligation:** not-required.

**Facets:** `noninitial-sibling-team-number`, `team-number-selects-sibling-team`, `parent-established-object`, `invalid-nonsibling-team-number`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
TEAM_NUMBER validity outside the initial team requires multi-image team construction and
is not converted into a mandatory static diagnostic. Future observations must avoid
using a nonexistent image or invalid team as evidence.

**Dependencies:** 4.2;5.3.4;8.5.6.1;9.6R928/C934/p5;11.1.5.1-.2 CHANGE TEAM;11.7.9 FORM
TEAM;16.10.2.34;19.5.1.6.

### S9.6-005: TEAM_NUMBER in the initial team names the initial team and requires initial-team establishment

**Source:** 9.6 p3, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** If TEAM_NUMBER= appears while the current team is the initial team, its scalar integer
value shall be the team number for the initial team, and the object shall be an
established coarray in the initial team.

**Diagnostic obligation:** not-required.

**Facets:** `initial-team-number-value`, `initial-team-established-object`, `noninitial-number-in-initial-team-invalid`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
The standard text does not state a literal value for the initial team's team number
here; future controls should use a standard inquiry or a separately reviewed FORM
TEAM/TEAM_NUMBER dependency rather than guessing.

**Dependencies:** 4.2;5.3.4;8.5.6.1;9.6R928/C934/p5;11.7.9;16.9 TEAM_NUMBER intrinsic;19.5.1.6.

### S9.6-006: An image selector without TEAM or TEAM_NUMBER uses the current team

**Source:** 9.6 p3, J3/24-007, 18 December 2023, physical PDF159. **Class:** Effect.

**Definition:** If neither TEAM= nor TEAM_NUMBER= specifies a different team under p3, the team of the
image selector is the current team. C934 makes TEAM and TEAM_NUMBER mutually exclusive
when either appears.

**Diagnostic obligation:** not-required.

**Facets:** `default-current-team-initial`, `default-current-team-inside-change-team`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Current-team observations inside CHANGE TEAM require a multi-image/team execution
profile and valid coarray association; this packet supplies no such case.

**Dependencies:** 4.2;5.3.4;9.6R928/C934;11.1.5.1-.2;11.7.9.

### S9.6-007: NOTIFY assignment atomically increments the corresponding notify variable without waiting

**Source:** 9.6 p4, J3/24-007, 18 December 2023, physical PDF159. **Class:** Effect.

**Definition:** Execution of an intrinsic assignment statement whose variable designator has a NOTIFY=
image-selector-spec atomically increments the count of the corresponding notify variable
on the image specified by the image selector, and the assignment does not wait for that
image to execute a corresponding NOTIFY WAIT statement.

**Diagnostic obligation:** not-required.

**Facets:** `assignment-variable-notify`, `corresponding-notify-variable-incremented`, `assignment-does-not-wait`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
NOTIFY observations require multi-image execution, valid NOTIFY_TYPE variables, and
corresponding NOTIFY WAIT semantics from 11.6; this packet records only pending source
plans.

**Dependencies:** 4.2;9.6R928/C933;10.2 intrinsic assignment;11.6R1166-R1167/C1177-C1178/p1-p10;16.10.2
NOTIFY_TYPE.

### S9.6-008: An image selector specifies an existing image index in its selected team

**Source:** 9.6 p5, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** An image selector shall specify an image index value that is not greater than the number
of images in the team of the image selector. That image index identifies the image with
that index in that team. The selected team is supplied by p3, and the image index value
is determined from the cosubscript list under p2.

**Diagnostic obligation:** not-required.

**Facets:** `image-index-within-team-size`, `image-index-identifies-image-in-team`, `image-index-too-large-invalid`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Runtime-valued image-count and team membership conditions are not static diagnostic
obligations in this packet. Future invalid-image tests must not use a reference to a
nonexistent image as observational evidence.

**Dependencies:** 4.2;5.3.4;9.6p2-p3;16.9 NUM_IMAGES/THIS_IMAGE inquiry intrinsics.

### S9.6-009: STAT in an image selector defines the STAT variable with failed-image or zero status

**Source:** 9.6 p6, J3/24-007, 18 December 2023, physical PDF159. **Class:** Effect.

**Definition:** Execution of a statement containing an image-selector with a STAT= specifier causes the
stat-variable to become defined. If the designator is part of an operand that is
evaluated or is a variable being defined or partly defined, and the object designated is
on a failed image, the stat-variable is defined with STAT_FAILED_IMAGE from
ISO_FORTRAN_ENV; otherwise it is defined with zero.

**Diagnostic obligation:** not-required.

**Facets:** `stat-variable-defined`, `stat-zero-on-nonfailed-image`, `stat-failed-image-value`, `failed-image-premise-limited-to-evaluated-or-defined-designator`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Failed-image observations require a processor/profile that can detect failed images; the
value of a coindexed object on a failed image is processor dependent and must not be
used as evidence.

**Dependencies:** 4.2;5.3.6;9.6R928/C935/p7;9.7R946 stat-variable;16.10.2.28 STAT_FAILED_IMAGE;16.10.2
ISO_FORTRAN_ENV.

### S9.6-010: STAT variables in image selectors are independent of same-statement evaluation and side effects

**Source:** 9.6 p7, J3/24-007, 18 December 2023, physical PDF159. **Class:** Restriction.

**Definition:** The denotation of a stat-variable in an image selector shall not depend on the
evaluation of any entity in the same statement. The value of an expression shall not
depend on the value of any stat-variable that appears in the same statement. The value
of a stat-variable in an image selector shall not be affected by execution of any part
of the statement, except through whether the image specified by the image selector has
failed.

**Diagnostic obligation:** not-required.

**Facets:** `stat-variable-denotation-independent`, `expression-value-independent-of-stat-variable`, `stat-variable-value-not-otherwise-affected`.

**Oracle:** Every facet is a pending source plan. Positive plans use independent literal values,
inquiry results, or synchronization observations that first establish definedness and
reached execution. Negative plans use an otherwise legal source and a minimal repair,
with attribution to the stated 9.6 rule or to an explicit dependency rather than an
unrelated parse, declaration, unsupported coarray profile, runtime launch failure, or
compiler agreement.

**Oracle limitation:** This source-only catalogue creates no Fortran test program, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
The exact boundary of 'denotation depends on evaluation of any entity in the same
statement' is source-sensitive for array-element STAT variables; this ambiguity is
recorded for independent review and no mandatory static diagnostic is claimed.

**Dependencies:** 4.2;9.6R928/C935/p6;9.7R946 stat-variable;10.1 expression evaluation;16.10.2.28.

<!-- END GENERATED 9.6 -->
