# Additional catalogue and fixture calibrations

These are deliberately partial catalogues. The generic source census lists
the entire corresponding subclauses, and unresolved passages remain visible.
Definitions below are generated from `doc/catalogues/`; do not edit the
generated regions by hand.

## Fixed-form continuation

The fixture uses actual fixed-form column positions, CRLF records, and no
in-band test directives. Its bytes are copied and hashed before compilation.
Its original execution ID and numeric/punctuation facets are preserved.
The draft fixed-source work unit now accounts for both paragraphs and the
note of 6.3.3.3, including the commentary premise and intervening comments.
New controls use exact 72-character records. The original short CRLF records
remain a processor-input calibration, not evidence of source-line length.
The corrected and extended requirement material stales the earlier fixture
approval; independent re-review is required, not performed by the author.

<!-- BEGIN GENERATED 6.3.3.3 -->

### S6.3.3.3-001: Fixed-form continuation uses character position six

**Source:** 6.3.3.3 p1; J3/24-007, 18 December 2023, PDF page 73, printed page 59, lines 8-10. **Class:** Effect.

**Definition:** Outside commentary, position 6 distinguishes an initial line from a continuation line.
Blank or zero starts a new statement with its field beginning in position 7. Any other
character in position 6 makes positions 7 through 72 continue the preceding noncomment
line. The indicator and label field do not become statement text. Commentary takes
precedence: punctuation in position 6 of an already recognized comment line has no
continuation meaning. A continuation needs a preceding noncomment line, not merely a
preceding comment.

**Diagnostic obligation:** required.

**Facets:** `numeric-indicator`, `punctuation-indicator`, `letter-indicator`, `blank-initial`, `zero-initial`, `column-seven`, `column-72`, `split-token`, `continued-literal-padding`, `indicator-excluded`, `commentary-precedence`.

**Oracle:** Preserve fixed_form/fixture.json, source.f, and execution ID
S6_3_3_3_001_valid__verbatim: its numeric and exclamation continuations still require
stdout FIXED=3,9. New exact-width controls check representative nonzero digit, letter,
underscore, ampersand, asterisk, exclamation and semicolon indicators against
independent sums; blank and zero initial lines against distinct assigned values; tokens
split across line boundaries; and a continued literal containing A, 59 explicit padding
blanks, and B. The latter distinguishes physical positions 7 and 72 and excludes the
indicator from the value. The separate orphan restriction and its admission-only repair
belong to S6.3.3.3-003.

**Oracle limitation:** The two original facet meanings and execution ID are append-only. The old short CRLF
file is a processor-input calibration: its preserved bytes do not prove the exact-72
source-line requirement. Clarifying the requirement material legitimately stales its
earlier fixture approval; this draft does not reapprove it. The finite indicator classes
do not claim all processor characters, arbitrary controls, tab expansion, or a mandatory
currency graphic. A semicolon on a preceding line may start the statement being
continued; 'preceding noncomment line' must not be replaced by 'preceding complete
statement'. Diagnostic capability for disallowed Clause 6 forms does not mandate fatal
rejection.

**Dependencies:** 6.3.3.1 (72-character default-kind lines and blank insignificance), 6.3.3.2 (comment
recognition), 6.3.3.4 (semicolon and continuation exceptions), and 6.3.3.5 (blank
continuation label fields and END restrictions). 3.21/R724 define the literal context.
6.1.1/6.1.6 retain processor repertoire restrictions; column 6 is not permission to
assume arbitrary extra source characters. 4.2 p2(5), PDF page 46, supplies the
diagnostic capability.

### S6.3.3.3-002: Comments do not continue but can intervene in a continued statement

**Source:** 6.3.3.3 p2; J3/24-007 PDF page 73, printed page 59, line 11. **Class:** Effect.

**Definition:** A comment line is not a statement to be continued. A character that would be a
continuation indicator outside commentary does not continue a comment or turn its next
physical line into commentary. Conversely, any number of intervening comment lines can
separate the noncomment portions of a continued statement. Initial and continuation
status is determined only after recognizing commentary.

**Diagnostic obligation:** not-required.

**Facets:** `comment-marker-is-inert`, `following-initial-is-executable`, `intervening-comment-kinds`.

**Oracle:** One exact-width program puts nonblank position-6 characters inside C, asterisk and
early-exclamation comments, plus a separate all-blank comment line, between x=1 and a
genuine continuation +2, checking 3. A subsequent comment with punctuation is followed
by a fresh initial assignment to an initialized sentinel, checking 7. Comments
containing statement-looking text never become an expression operand or swallow the next
initial line.

**Oracle limitation:** An intervening comment before an otherwise legitimate continuation is conforming, not a
comment-continuation negative. The orphan case belongs to S6.3.3.3-003, not to a claim
that a comment itself continues. This effect oracle does not demand a diagnostic for a
harmless continuation-looking character within commentary, or claim unbounded processor
storage.

**Dependencies:** 6.3.3.2 comment-line recognition is applied before 6.3.3.3 p1. 6.3.3.4 p1 terminates
only a statement that is not continued. The source's informative note explains this
precedence for exclamation and semicolon in position 6.

### S6.3.3.3-003: A continuation line needs a preceding noncomment line

**Source:** 6.3.3.3 p1, final sentence; J3/24-007 PDF page 73, printed page 59, lines 9-10. **Class:** Restriction.

**Definition:** The first noncomment line cannot be a continuation: there is no preceding noncomment
line for its statement field to extend. A preceding comment does not supply the missing
initial line. This is distinct from the permitted occurrence of comments between an
initial line and a genuine continuation.

**Diagnostic obligation:** required.

**Facets:** `preceding-noncomment-required`.

**Oracle:** After one comment line, the PROGRAM line has a nonzero continuation indicator in column
6. Require a report on that exact PROGRAM line, allowing Flang's specifically matched
scanning warning as well as a located error. Changing just that indicator to blank
repairs the source; the repair is explicitly a compile-only positive control, not
runtime continuation-effect evidence.

**Oracle limitation:** There is no earlier statement whose continuation could make this text legal, and no
invalid label field. The comment itself is never treated as a continued statement.
Unlocated, wrong-line, unrelated and earlier-step reports, crashes and timeouts cannot
satisfy the diagnostic contract.

**Dependencies:** 6.3.3.2 recognizes the preceding comment before 6.3.3.3 classifies the PROGRAM line.
R1401/R1402/R1403 provide the otherwise complete main-program syntax. 4.2 p2(5), PDF
page 46, requires reporting capability for this disallowed source form without requiring
fatal rejection.

<!-- END GENERATED 6.3.3.3 -->

## STOP and external I/O expectations

**11.4 source review is recorded in batch062.** Effective status remains
`Registry.catalogue_review_state("11.4")`. All ten original base units of
J3/24-007, December 18, 2023, are accounted from physical PDF228-229,
including NOTE2 before the actual next heading, 11.5. The pinned 688-page
PDF has SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
Every new facet remains pending; source accounting is not independent
source approval, fixture evidence or whole-standard completion.

The source initiates normal termination with `STOP 200`. Fortran makes
the process-status mapping a recommendation and processor-dependent
interface, not a universal requirement. This fixture explicitly chooses
the `posix-stop-code` execution profile, checks stdout and a closed output
file, and expects status 200. It is not a compiler crash or a generic
"any nonzero status passes" negative test.

The entire S11.4-001 record, its two source anchor IDs and
`S11_4_001_valid__stop_io` are preserved. Its input7, stdout `INPUT=7`,
explicitly closed file containing49 and after-STOP marker retain the
existing external-driver contract. This is not evidence of implicit file
closing or a new execution. The historical processor modes, fingerprints
and raw review are not relabelled by this source expansion.

The new syntax plans separate code and QUIET optionality, scalar/type/kind
premises and source-form owners. An ordinary nonconstant scalar expression
is not excluded just because it is not a literal; default logical kind is
not required for QUIET. Unsupported kinds/facilities or unrelated syntax
errors cannot stand in for an intended diagnostic.

Normal/error termination and image states belong to5.3.4-5.3.7. In this
pinned draft,11.6 is NOTIFY WAIT, not the termination subclause. A single
process crash or nonzero shell status is not evidence of program-wide
ERROR STOP propagation. Image/team/segment and complete-lifecycle gates
remain explicit; the recommendation to propagate quickly has no prescribed
numeric deadline.

The p2 status mappings and p3 formatted-code-output advice remain
recommendations, not universal exit values, streams or wording. The
existing `p2.integer-status` anchor is now classified as a recommendation,
without changing the S11.4-001 requirement or its selected profile.
Processor-dependent availability of a specified code is a separate effect.

When QUIET is omitted or false and an exception is signaling on that image,
p3 requires an identifying warning on ERROR_UNIT. With explicit true
QUIET, p4 requires suppression of exception and stop-code output. Neither
condition is weakened to advice. IEEE support, halting and procedure-entry
flag behavior require actual qualification; a signaling flag is not a
signaling-NaN value or a trap oracle. ERROR_UNIT may equal OUTPUT_UNIT and
is not universally OS stderr. Silence without proven statement entry and
termination cannot establish suppression.

Both original notes remain informative, including the limited-range and
low-eight-bit example. No fixtures, profiles, driver changes, compiler runs,
links, SourceUses entries, baseline changes or approvals are added. Other
sections in this shared view retain their independent content and status.

<!-- BEGIN GENERATED 11.4 -->

### S11.4-001: STOP initiates normal termination

**Source:** 11.4 p1; the integer process-status recommendation in p2 is a separate profile qualification. **Class:** Effect.

**Definition:** Executing STOP initiates normal termination. The optional integer process-status mapping
is processor-dependent and recommended rather than universally required.

**Diagnostic obligation:** not-required.

**Facets:** `normal-termination`, `posix-stop-code`.

**Oracle:** Use an external driver to supply input, inspect stdout and a closed output file, and
judge termination. The posix-stop-code facet explicitly chooses status 200 as a
processor-profile expectation; it must not be mistaken for a compiler crash or silently
promoted to a universal Fortran requirement.

### R1162: STOP has independently optional stop-code and QUIET parts

**Source:** 11.4 R1162, J3/24-007, 18 December 2023, physical PDF228, printed214, line15. **Class:** Syntax.

**Definition:** A STOP statement has an optional stop-code followed by an independently optional comma
and QUIET=scalar-logical-expr. The code may be omitted while QUIET is present. QUIET is
a scalar logical expression, not necessarily a literal or constant expression, and this
production does not require default logical kind. Stop-code type/kind and source-form
rules retain their own owners.

**Diagnostic obligation:** required.

**Facets:** `no-code-form`, `code-and-quiet-optionality`, `quiet-scalar-logical`, `quiet-expression-admission`, `separator-and-order-source-gate`.

**Oracle:** Source-valid compile/positive-controls and single-predicate diagnostic/repair pairs in
ordinary program contexts, with complete source, exact intended causes and legitimate
origins reviewed before any fixture.

**Oracle limitation:** 4.2 requires reporting capability, not fatal rejection, fixed wording or a printed code.
Unsupported STOP/QUIET facilities, source echoes, other errors and internal/resource
failures are not qualifying diagnostics. No new fixture, role designation or runtime
evidence is supplied.

**Dependencies:** 4.1.1-.4, especially R403/C401;4.2p2;6.3.2/.3;10.1.9.1 C1007;11.4
R1164/C1176;14.1;canonical S11.4-001.

### R1163: ERROR STOP has independently optional stop-code and QUIET parts

**Source:** 11.4 R1163, physical PDF228, printed214, line16. **Class:** Syntax.

**Definition:** An ERROR STOP statement has an optional stop-code and an independently optional
following comma-QUIET scalar-logical expression. Its syntax does not require a code, a
constant QUIET value or default logical kind. Admission of the statement is distinct
from executing error termination and from the source-form rules for its two keywords.

**Diagnostic obligation:** required.

**Facets:** `no-code-form`, `code-and-quiet-optionality`, `quiet-scalar-logical`, `quiet-expression-admission`, `separator-and-order-source-gate`, `source-form-keyword-boundary`.

**Oracle:** Complete syntax admissions and genuinely source-isolated diagnostic repairs, without
executing the ERROR STOP programs or duplicating canonical expression/source-form cases.

**Oracle limitation:** No fatal-status, standardized-English, rule-code or unsupported-feature proxy. This
source-only entry does not claim an error-termination trace, a process-status value or a
multi-image result.

**Dependencies:** 4.1.1-.4;4.2p2;6.3.2.2p2-p3/Table6.2;6.3.3.1;10.1.9.1 C1007;11.4
R1164/C1176;14.1;S11.4-002.

### R1164: A stop-code is scalar default character or scalar integer

**Source:** 11.4 R1164, physical PDF228, printed214, lines17-18. **Class:** Syntax.

**Definition:** A stop-code is a scalar default-character expression or a scalar integer expression;
C1176 additionally restricts the integer alternative to default kind. These are
expressions, not literal-only or constant-expression productions. Character length,
integer sign and host process-status representability do not supply additional local
restrictions.

**Diagnostic obligation:** required.

**Facets:** `default-character-admission`, `integer-admission`, `defined-expression-admission`, `other-type-source-gate`, `scalar-source-gate`, `default-character-kind-source-gate`.

**Oracle:** Finite complete type/rank/expression admissions and source-isolated canonical negatives.
Defined scalar values and actual supported kinds are prerequisites, independent of any
compiler's diagnostic wording.

**Oracle limitation:** No new BOZ claim, undefined operand evaluation, character-storage model or universal
process-status truncation oracle. Numbered reporting capability is not required
rejection or a prescribed message.

**Dependencies:** 4.1.3 R403/C401;4.2p2;7.4.3.1;7.4.4.1/.2;10.1.9.1 C1008/C1009;10.1.9.2;11.4
C1176/p2/note2.

### C1176: An integer stop-code has default kind

**Source:** 11.4 C1176 associated with R1164, physical PDF228, printed214, line19. **Class:** Restriction.

**Definition:** The scalar integer expression used as a stop-code has default integer kind. The
restriction applies to the integer alternative, not to QUIET or character length.
Default kind is identified by the language's kind relation, not by a fixed kind number,
storage width or process-status range.

**Diagnostic obligation:** required.

**Facets:** `default-kind-admission`, `supported-nondefault-kind-exclusion`, `kind-identity-source-boundary`.

**Oracle:** An actually supported nondefault-kind violation paired with a valid default-kind
control, with precise source attribution and complete cause review. Admission is
compile/positive-control evidence, not a status-value effect.

**Oracle limitation:** No kind=4/8 or word-size assumption, unsupported-kind credit, narrowing/overflow repair,
mandatory fatal status or printed C1176 requirement. The unchanged status200 calibration
is not a new C1176 case.

**Dependencies:** 4.1.2;4.2p2;7.4.3.1p1-p4/p6;10.1.9.1/.2;11.4 R1164/p2/note2;actual processor kind
capability.

### S11.4-002: Executing ERROR STOP initiates error termination

**Source:** 11.4 p1 second sentence, physical PDF228, printed214, lines20-21; canonical termination semantics are5.3.7. **Class:** Effect.

**Definition:** Execution of ERROR STOP initiates error termination, not normal termination, return from
a procedure or a failed-image event. Under5.3.7, initiation on an image propagates to
all images that have not already initiated error termination; program termination occurs
when all images have terminated or failed. The recommendation to propagate as quickly as
possible is not a numeric timing guarantee. A nonzero shell status alone does not
establish these semantics.

**Diagnostic obligation:** not-required.

**Facets:** `initiating-image`, `program-wide-image-propagation`, `stopped-and-failed-image-source-boundary`, `team-and-segment-source-gate`.

**Oracle:** Real run/effect evidence through a source-reviewed termination/lifecycle mechanism or
qualified canonical reuse. Entry, intended statement execution and whole-run completion
must be externally established with independent events and correct image/configuration
bindings.

**Oracle limitation:** The applicable termination owner in this pinned draft is5.3.7, not11.6, which describes
NOTIFY WAIT. No mandatory error exit code, signal, crash, post-error file flush, C ABI
or fixed propagation deadline is inferred. Missing lifecycle/launcher capability leaves
the facet pending or an observation unqualified, not passed.

**Dependencies:** 5.3.4-.7;11.5;11.7.1/.2;11.4 R1163/p2;4.2p1-p2/p5-p8;canonical termination, image/team
and segment owners.

### S11.4-003: A terminating image's specified stop code is made available by a processor-dependent method

**Source:** 11.4 p2 first sentence, physical PDF228, printed214, lines22-23. **Class:** Effect.

**Definition:** When an image is terminated by STOP or ERROR STOP, a specified stop code is made
available in a processor-dependent manner. The method is not universally a process exit
status, stdout, stderr, formatted text or an exact message. The integer/other-status
recommendations and the formatted-output recommendation are separately classified;
QUIET=true suppresses code output without defining an exit status or erasing every
possible non-output availability mechanism.

**Diagnostic obligation:** not-required.

**Facets:** `integer-code-interface`, `character-code-interface`, `statement-kind-and-termination-binding`, `quiet-true-nonoutput-interface`.

**Oracle:** An actual independently specified code joined to a reviewed processor-defined interface
and successful complete execution evidence. Unknown or unavailable mechanisms are
explicit source/documentary/profile gates, not generic output or exit-code fallbacks.

**Oracle limitation:** Documentary/profile prerequisites are qualification gates, not a new universal
documentation mandate. No universal process concept, exact code mapping, 8-bit
truncation, status200, nonzero error status or literal STOP/ERROR STOP text is added.
All new facets remain pending; historical observations and S11.4-001 remain unchanged.

**Dependencies:** 11.4 R1164/C1176/p2-p4/note2;5.3.4-.7;4.2p5-p8;actual processor interfaces;unchanged
S11.4-001 and its explicitly selected posix-stop-code profile.

### S11.4-004: Without QUIET=true, signaling exceptions require an identifying warning on ERROR_UNIT

**Source:** 11.4 p3 condition and first bullet, physical PDF228, printed214, lines29-32. **Class:** Effect.

**Definition:** If QUIET is omitted or its scalar logical expression is false and any exception is
signaling on the terminating image, the processor issues a warning identifying which
exceptions are signaling, on the unit identified by ISO_FORTRAN_ENV's ERROR_UNIT. This
conditional runtime warning is required, unlike the following stop-code-output
recommendation. The metadata's not-required compile-diagnostic obligation does not
weaken that runtime requirement.

**Diagnostic obligation:** not-required.

**Facets:** `quiet-omitted`, `quiet-false`, `multiple-signaling-flags`, `error-unit-routing`, `terminating-image-and-scope-state`.

**Oracle:** Real run/effect records join supported flag setup, independently specified expected
identities, the actual terminating statement/image, ERROR_UNIT routing and externally
observed completion. Compiler/configuration-specific output decoding needs review and
may not accept generic exception-looking text.

**Oracle limitation:** IEEE modules and some flags are processor dependent; IEEE_SUPPORT_FLAG and any
IEEE_SUPPORT_HALTING prerequisites must be honored. Do not call IEEE_SET_HALTING_MODE
when support is false or assume an initial halting mode. Signaling flags are not
signaling-NaN values or proof of a trap. The p3 second bullet remains a recommendation,
and no native observation/profile is authored here.

**Dependencies:** 11.4p3-p4;5.3.4p1/5.3.7;16.10.2.9;17.1-.3,
especially17.3p2-p3/p8/p10;17.6/.7;17.11.5/.6/.39/.40/.55/.56.

### S11.4-005: QUIET=true suppresses signaling-exception and stop-code output

**Source:** 11.4 p4, physical PDF228, printed214, lines35-36. **Class:** Effect.

**Definition:** When QUIET is present and its scalar logical expression is true, no output of signaling
exceptions or the stop code is produced. This is a required suppression for STOP and
ERROR STOP, not merely a recommendation. It does not suppress arbitrary earlier user
output, remove termination, prescribe a process status, clear IEEE flags or promise a
particular processor representation.

**Diagnostic obligation:** not-required.

**Facets:** `stop-code-output`, `signaling-exception-output`, `combined-code-and-flags`, `defined-quiet-expression`, `statement-kind-and-completion-guards`.

**Oracle:** A real executed true-QUIET statement and established code/flag premises, observed
through qualified output and lifecycle interfaces. Literal independent setup
expectations and complete traces must distinguish suppression from absent work or failed
execution.

**Oracle limitation:** No universal empty-stderr or empty-all-output assertion, forced zero/nonzero status, C
interface, flush guarantee or physical descriptor claim. Stop-code availability and
status/output recommendations retain their separate meanings. Missing
mode/profile/routing/lifecycle support leaves evidence unqualified; all new facets are
pending.

**Dependencies:** 11.4 R1162-R1164/C1176/p2-p4;5.3.4-.7;16.10.2.9;17.1/.3/.6/.7 and relevant flag/halting
procedures;S11.4-003/-004;unchanged S11.4-001.

<!-- END GENERATED 11.4 -->

## Fortran/C interoperability

The fixture compiles a Fortran module, a C implementation, and a Fortran
caller separately, then links their objects. This verifies real companion-
processor argument/result behavior rather than only Fortran-side C_PTR
inquiries. C descriptors and other procedure-interface cases remain
explicitly unresolved in this partial catalogue.

<!-- BEGIN GENERATED 18.3.7 -->

### S18.3.7-001: Interoperable ordinary arguments and scalar results correspond across C and Fortran

**Source:** 18.3.7 p2 items (2)(a), (4), and the interoperable-entity alternative of (5); p3. Eligibility also depends on 18.3.6. **Class:** Effect.

**Definition:** For an eligible BIND(C) interface matching a C prototype, VALUE scalars, non-VALUE
interoperable array arguments, and an interoperable scalar result correspond to the
appropriate C values, pointers, and result in matching argument positions.

**Diagnostic obligation:** not-required.

**Facets:** `value-scalar`, `array-pointer`, `scalar-result`.

**Oracle:** Compile a Fortran interface/wrapper module, a C function, and a Fortran caller
separately. The C function receives a count by value and an integer array by pointer,
mutates the array, and returns a checksum. Check independently specified values and
stdout after linking the declared objects.

<!-- END GENERATED 18.3.7 -->

## Verbatim EOF rejection

`tests/fixtures/missing_end/fixture.json` associates R1401 with a raw,
unterminated main program. The Fortran file has no error marker and no
final newline. An external EOF predicate accepts a normal parser
diagnostic, including an unlocated EOF report, but not an unrelated
compiler crash or an earlier build failure.
