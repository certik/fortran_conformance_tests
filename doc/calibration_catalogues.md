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

The source initiates normal termination with `STOP 200`. Fortran makes
the process-status mapping a recommendation and processor-dependent
interface, not a universal requirement. This fixture explicitly chooses
the `posix-stop-code` execution profile, checks stdout and a closed output
file, and expects status 200. It is not a compiler crash or a generic
"any nonzero status passes" negative test.

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
