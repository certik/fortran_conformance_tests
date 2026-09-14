# Fortran 2023 section 6.4: including source text

**Draft authoring scope:** J3/24-007, dated 18 December 2023, PDF pages 73-74
(printed pages 59-60), paragraphs 1-7 and the unnumbered note. The pinned PDF
SHA-256 is
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
Clause 7 starts after this scope. No original body text or PDF is committed.
The catalogue remains draft; fixture approval and independent source review
belong to the integrator.

`doc/catalogues/include_lines.json` accounts for all eight base units and
28 necessary fine units, including all four note bullets and their compound
conditions. It allocates only `S6.4-001` through `S6.4-008`. The 61 named
facets distinguish effects, restrictions and controls; two are explicitly
pending. Source accounting is not evidence that the facets executed or passed.

## Source and interface boundaries

An INCLUDE line is neither an ordinary Fortran statement nor a preprocessing
directive. Labels, semicolons and ordinary statement continuation therefore
cannot be assumed to work on it. Conversely, included text can contain
labeled statements, internal continuation, incomplete constructs completed
by the host, and nested INCLUDE lines, subject to the resolved boundary rules.
The source explicitly prohibits cycles but does not specify a numeric nesting
limit. Reusing a sidecar after an earlier inclusion finishes is not a cycle.

The byte fixtures select free or fixed form explicitly in complete typed
manifests. Every input is declared and staged beside its driver, so source
directory and process current directory agree. Flat lower-case ASCII filenames
and LF record delimiters are a qualified source interface of the observed
processors, not a universal interpretation of the character constant. Fixed
source records have exactly 72 bytes before LF; no tab, non-ASCII character,
incidental dollar symbol, short-line padding or overlong-line truncation is
needed. The `.inc` suffix does not select a different source form.

The numeric character-kind selector control needs a documented supported
numeric value and source-reference interface. Free-form INCLUDE with no
separator before its literal needs independent interpretation review because
the definition of an unqualified keyword is tied to statements. Neither issue
is decided by a green compiler result. Unusual filename quoting, empty
filename interpretation, search order and non-filename interfaces are not
claimed. The note's column-73 dual-form technique remains informative,
source-only guidance pending an independently qualified record-field mapping;
it is not a mandatory 73-character fixed-line test.

## Fixtures and observation contract

`tools/generate_include_fixtures.py` deterministically writes only
`tests/fixtures/include_*` manifests and their declared assets. It preserves
column fields, blank/comment boundary records, and the genuinely empty
included file. Its `--check` mode checks both bytes and the complete asset set.
No ordinary `tests/clause06` source is needed: all cases either include a
sidecar or need external byte/line metadata.

Each negative uses compile-only `diagnose`, not mandatory fatal rejection.
The predicates point to the actual source record, including `.inc` assets.
The first attempted INCLUDE record is retained for a split INCLUDE; no
invented statement span or EOF line is substituted. Errors at ordinary exit
statuses can corroborate; nonfatal reports need specific family, severity
and message qualification. Wrong steps, wrong locations, unrelated errors,
driver summaries, compiler crashes, resource failures and timeouts do not.
Four trailing-text negatives explicitly allow the exact, located Flang
`excess characters after path name [-Wscanning]` warning. This reports
invalid input at an ordinary successful exit; it does not make that input
conforming. A generic nesting-limit message saying `possibly circular` is
not accepted as a cycle-specific diagnostic.
Every negative has a conforming repair with an independent scalar assertion.
Boundary repairs move a single host record into the included asset, retaining
the same arithmetic rather than merely deleting the feature.

At baseline `965afb6`, the reference location parser recognizes only
`.f90`, `.f`, `.c` and `.h`. Real diagnostics from `.inc` files must remain
visible as parser limitations, not be hidden by renaming the assets or
changing the intended witness. The GNU single-source-driver exception cannot
apply: these sources spell INCLUDE and have multiple declared inputs.
Unlocated include diagnostics or reports attributed to the host need separate
review; adding an extension does not authorize inventing a location.

For locally registered draft observations:

```sh
python3 -B tools/generate_include_fixtures.py --check
python3 -B tests/suite_data.py --render
python3 -B tests/run_tests.py --list -t S6.4
python3 -B tests/run_tests.py --allow-unreviewed --no-skips --timeout 5 \
  -t S6.4 --reference gfortran --reference flang --report ABSOLUTE_ARTIFACT
```

The five-second process-group timeout is required for the two cycle
observations; never invoke those compilers unbounded. Exhausting a
processor's nesting limit does not itself satisfy the cycle-specific oracle.
The local index registration is deliberately excluded from the draft commit.
No source approval, fixture review or expected-failure baseline is updated.

<!-- BEGIN GENERATED 6.4 -->

### S6.4-001: The INCLUDE form uses a character literal, not an arbitrary expression

**Source:** 6.4 p1, displayed form; J3/24-007, 18 December 2023, PDF page 73, printed page 59, lines 25-27. **Class:** Syntax.

**Definition:** Source incorporation uses the INCLUDE spelling followed by a char-literal-constant. Both
literal delimiters are available under R724. A character variable, named character
constant, or concatenation expression is not this syntactic class. Case equivalence
outside character context and the selected source form's blank rules still apply. An
assignment to a variable named include, or INCLUDE-like text inside a comment or
character literal, is not an INCLUDE line. This form does not specify a preprocessing
directive such as #include.

**Diagnostic obligation:** required.

**Facets:** `free-apostrophe`, `free-quotation`, `case-equivalence`, `fixed-blank-spelling`, `include-name-context`, `comment-literal-context`, `nonliteral-source-diagnostic`, `expression-source-diagnostic`, `free-no-separator-interpretation`.

**Oracle:** Separate controls use apostrophe and quotation delimiters, mixed letter case, and a
fixed-form spelling with interspersed blanks and no blank before the literal. The fixed
records are exactly 72 ASCII characters. Another control assigns to include inside the
included text. Comment and character-literal controls retain INCLUDE and #include text
as data or commentary while a real INCLUDE updates an initialized scalar exactly once.
Two diagnose pairs replace a literal by a declared character constant, or add
concatenation with an empty literal. Their repairs restore the literal form and run the
independently known value 23. The concatenation case explicitly permits the located
Flang warning 'excess characters after path name [-Wscanning]' through an exact
compiler/severity/message predicate; it is a report of invalid input, not a conforming
compile-only result.

**Oracle limitation:** All source references use declared, flat, lower-case ASCII sidecars at the staged root.
Treating their literals as filenames is an explicitly qualified processor interface, not
the universal interpretation required by p7. The source and current directory coincide,
so these cases establish no search-order rule. An absent-file or unsupported-feature
message is not the intended syntax observation. Delimiter escaping in unusual filenames,
empty filename interpretation, Unicode, tab expansion, and a numeric kind convention are
not inferred. The special GNU single-source-driver attribution is never applicable to
these INCLUDE-bearing, multi-input fixtures.

**Dependencies:** 4.1.1 p1 and 4.1.4 p1, PDF 44-45, distinguish syntactic forms and statements; 5.5.2 p1,
PDF 65, defines keyword usage. 3.21, PDF 21, and 6.1.2 p3, PDF 67, govern character
context and case. 6.3.2.2, PDF 71, and 6.3.3.1 p2, PDF 72, govern source-form blanks.
R603 and R724/C732, PDF 68/85-86, supply names and literals. 4.2 p2(5), PDF 46, supplies
reporting capability rather than mandatory fatal rejection.

### S6.4-002: An INCLUDE literal cannot select its kind with a named constant

**Source:** 6.4 p2; J3/24-007, 18 December 2023, PDF page 73, printed page 59, line 28. **Class:** Restriction.

**Definition:** The INCLUDE character literal cannot use a named constant as its kind selector. This is
a restriction on the selector's spelling, not a prohibition of all kind prefixes and not
a ban on a numeric selector merely because its value equals that of some named constant.
R709 and R724 otherwise allow a digit-string selector whose representation is supported;
omitting the prefix selects default character.

**Diagnostic obligation:** required.

**Facets:** `named-kind-diagnostic`, `omitted-kind-control`, `numeric-kind-control`.

**Oracle:** The negative declares an integer parameter ck = kind('a') and uses ck_'payload.inc'.
Thus the kind is supported and the parameter is declared; the intended defect is the
named selector in INCLUDE, not an unsupported kind or missing declaration. The minimally
repaired control removes only ck_ and checks that the included assignment produces 23.
Both versions declare the same existing sidecar.

**Oracle limitation:** A located source-form report is required; fatal rejection is not. Failure to open a
misinterpreted filename or failure of an unrelated feature is not corroboration. The
numeric-selector branch remains pending rather than being silently collapsed into the
default-character control.

**Dependencies:** R709, PDF 80, distinguishes a digit string from a scalar integer constant name. R724,
C732 and 7.4.4.3 p2, PDF 85, supply literal syntax, supported representation and the
default on omission. KIND supplies the known supported selector for the negative; its
general intrinsic semantics are uncredited context. 4.2 p2(5), PDF 46, applies to the
INCLUDE restriction.

### S6.4-003: An INCLUDE line occupies one source line at a statement position

**Source:** 6.4 p4, first clause; J3/24-007, 18 December 2023, PDF page 73, printed page 59, line 30. **Class:** Restriction.

**Definition:** An INCLUDE line occurs where a statement can occur and fits on one source line. Ordinary
statement continuation does not turn it into a multi-line statement: p3 explicitly says
it is not a Fortran statement. The selected source form controls layout. Being able to
join tokens or a literal in an ordinary statement does not authorize continuing an
INCLUDE line.

**Diagnostic obligation:** required.

**Facets:** `free-single-line`, `fixed-single-line`, `statement-position`, `free-token-continuation-diagnostic`, `free-literal-continuation-diagnostic`, `fixed-continuation-diagnostic`.

**Oracle:** Three pairs split the attempted INCLUDE between its spelling and literal in free form,
within the filename literal in free form, or onto a fixed-form column-six continuation.
Every intended filename names a declared sidecar. The repaired controls join those two
physical records into one INCLUDE line, without changing the program computation, and
check 23. The diagnostic anchor is the first physical record of the attempted INCLUDE,
not a fabricated statement span or an arbitrary whole-program recovery range.

**Oracle limitation:** A compiler that misreads a partial filename can emit an absent-file error; this is not
the intended source-form reporting oracle. Reports on a different record must remain
visible as attribution differences, not be silently widened. Statement-position controls
are finite executable-part witnesses. Specification, complete-unit and partial-construct
insertion are effects under S6.4-005, and are not automatically credited to this
restriction. No assumption about physical newline encodings beyond the declared LF
source interface is made.

**Dependencies:** 6.4 p3 and 4.1.4 p1 distinguish INCLUDE from -stmt forms. 6.3.1 p1/p3, PDF 71, defines
lines and source-form selection; 6.3.2.4 and 6.3.3.3, PDF 72-73, supply ordinary
continuation contexts without extending them to INCLUDE. 4.2 p2(5), PDF 46, requires
reporting capability.

### S6.4-004: An INCLUDE line has no label or other source text beside it

**Source:** 6.4 p4, remaining clauses and conclusion; J3/24-007, 18 December 2023, PDF page 73, printed page 59, lines 30-31. **Class:** Restriction.

**Definition:** Apart from blanks and an optional trailing comment, the INCLUDE line is the entire
source line. It has no statement label. A semicolon cannot attach a preceding or
following statement, or a second INCLUDE, to that line. An action-IF prefix likewise
cannot make INCLUDE an action statement. The exception for commentary does not permit
additional noncomment source after the literal.

**Diagnostic obligation:** required.

**Facets:** `sole-line-free`, `sole-line-fixed`, `leading-trailing-blanks`, `trailing-comment-free`, `trailing-comment-fixed`, `label-free-diagnostic`, `label-fixed-diagnostic`, `semicolon-before-free-diagnostic`, `semicolon-after-free-diagnostic`, `semicolon-before-fixed-diagnostic`, `semicolon-after-fixed-diagnostic`, `two-includes-diagnostic`, `action-if-diagnostic`.

**Oracle:** Free and fixed pairs isolate labels and statements before or after a semicolon; another
pair places two INCLUDE forms on one line. Repairs remove the label or replace just the
offending semicolon boundary by a new source record. An action-IF pair is repaired into
a block IF with INCLUDE on its own line. All repaired programs check a defined value.
Two additional controls retain surrounding blanks and a trailing comment ending in
ampersand, showing that commentary does not continue the INCLUDE. Fixed labels and
column-six fields are preserved exactly. The two trailing-statement negatives and the
two-INCLUDE negative allow only the observed, located Flang warning 'excess characters
after path name [-Wscanning]' with an exact family/severity/message predicate; a zero
compiler exit is then permitted by the reporting contract.

**Oracle limitation:** These are restrictions on the INCLUDE line, not on labels or semicolons in the included
text. S6.4-005 separately admits labeled included statements. An INCLUDE-like name
assignment is also not a forbidden INCLUDE. Rejection is not mandatory: specifically
qualified, located warnings or portability reports can satisfy diagnose, but unlocated
driver output cannot be guessed to originate in a sidecar. The source-form prohibition,
not a processor's extra preprocessing syntax, is the basis.

**Dependencies:** 6.3.2.3/6.3.3.2 define comments; 6.3.2.5/6.3.3.4 define ordinary statement separators,
which p3 does not transfer to INCLUDE. 6.3.2.6/6.3.3.5 supply statement-label contexts.
R1141 and the block-IF construct supply the minimal action-IF repair. 4.2 p2(5), PDF 46,
supplies the reporting obligation.

### S6.4-005: Included source replaces its INCLUDE line before program processing

**Source:** 6.4 p5, first two sentences; J3/24-007, 18 December 2023, PDF page 73, printed page 59, lines 32-34. **Class:** Effect.

**Definition:** The referenced source takes the place of the INCLUDE line before the resulting program
is processed. It can supply declarations, executable statements, construct fragments,
comments, or further INCLUDE lines; it need not be a self-contained program or a
complete construct. Nested INCLUDE lines undergo the same substitution. The expanded
program must still satisfy the applicable source-form, statement-ordering and other
language requirements, including p6's boundary restrictions.

**Diagnostic obligation:** not-required.

**Facets:** `specification-text`, `executable-order`, `repeated-nonrecursive-text`, `partial-construct`, `contained-subprogram`, `whole-program-unit`, `fixed-form-text`, `nested-replacement`, `empty-text`, `comment-only-text`.

**Oracle:** Eight effect fixtures check independent expected scalar results: declarations supply 35
used to produce 37; two nonrecursive insertions around host arithmetic produce 19; an
included open IF construct completed by the host produces 7; an included contained
function returns 43; an entire included main program checks 47; fixed-form text with a
complete internal continuation and a labeled statement produces 21; ordered nested
substitution produces 45; and empty/comment-only text leaves 17 unchanged. No oracle
relies solely on agreement with a separately compiled expansion of the same text. All
scalar sentinels and function results are explicitly assigned before observation.

**Oracle limitation:** The chosen flat-filename, ASCII/LF interface is qualified under p7, with every asset
staged beside its driver and explicit source-form selection. Inherited source form is
not selected by the .inc suffix. Two active inclusion levels are a finite observation,
not a universal promised maximum or a demand for unbounded resources. No source search
order, macro expansion, conditional preprocessing, automatic form switch, external I/O
round trip, or arbitrary shell build step is exercised. Passing effect cases do not
establish diagnostic coverage for the restrictions.

**Dependencies:** 6.3.1 p3 prohibits mixing source forms within a unit; 6.3.3.1/6.3.3.3/6.3.3.5 supply
exact-width fixed records, continuation and label fields. 5.1/R502 (PDF 53, lines 7-11)
and separately 5.3.2 p1 (PDF 57, lines 18-20) supply the ordering illustration. Clause 8
declarations, Clause 10 integer assignment/arithmetic, the block IF and internal
subprogram rules govern the expanded programs. 4.2 p2(1) retains size/complexity
qualifications; p6 governs processor-dependent provision/semantics, p7 recommends
limit/extension documentation, and p8 recommends methods/semantics documentation.

### S6.4-006: Active inclusion cannot lead back to the same source text

**Source:** 6.4 p5, final sentence; J3/24-007, 18 December 2023, PDF page 73, printed page 59, lines 35-36. **Class:** Restriction.

**Definition:** Following an INCLUDE reference, at no further nesting level may its expansion include
that same source text again. Both a direct self-edge and a multi-source cycle violate
the rule. A later independent inclusion after an earlier inclusion has finished is not
that recursion; nor is reuse in two completed sibling branches. The separate
processor-dependent maximum nesting depth is not a universal numeric language limit.

**Diagnostic obligation:** required.

**Facets:** `direct-cycle-diagnostic`, `indirect-cycle-diagnostic`, `acyclic-direct-control`, `acyclic-indirect-control`, `sibling-reuse-control`.

**Oracle:** Two compile-only diagnose fixtures contain respectively loop.inc including itself and
first.inc -> second.inc -> first.inc. Their declared locations are the include edge
closing the cycle, in loop.inc or second.inc, line 1. A repair replaces just that cyclic
edge with value = value + 1; both repaired programs check 1. A separate sibling-reuse
control includes the same leaf twice through different completed branches and checks 3.
These use actual repeated asset identity, not equal text in unrelated files, path
aliases or filesystem links.

**Oracle limitation:** Run every cyclic observation only through the existing process-group timeout; the author
command uses --timeout 5. A timeout, crash, resource failure, or generic maximum-depth
exhaustion is a failure, not proof of cycle reporting. The diagnostic message must
identify recursion, a detected cycle, or reinclusion of the same source; the observed
Flang limit report saying 'possibly circular' does not suffice. The reference parser at
baseline965afb6 recognizes only .f90/.f/.c/.h locations, so genuine .inc reports can
remain parser-blocked. Do not rename the intended assets or use GNU single-source-driver
attribution to hide this limitation.

**Dependencies:** 6.4 p5's depth-limit sentence is separately accounted as processor dependent. 4.2 p2(5),
PDF 46, supplies reporting capability for the prohibited source relationship; p2(1) does
not turn resource exhaustion into such a report. The acyclic controls use only small
integer assignment and the same flat-file source interface.

### S6.4-007: The first resolved included statement line cannot be a continuation

**Source:** 6.4 p6, first boundary condition; J3/24-007, 18 December 2023, PDF page 74, printed page 60, lines 1-2. **Class:** Restriction.

**Definition:** After resolving the INCLUDE, its first statement line is an initial line, not a
continuation of a statement started outside the included text. Leading comments and
blank lines do not change which line is the first statement line. Resolution includes
nested INCLUDE replacement. Complete statements may still use continuation wholly within
included text.

**Diagnostic obligation:** required.

**Facets:** `free-first-continuation-diagnostic`, `fixed-first-continuation-diagnostic`, `nested-first-continuation-diagnostic`, `leading-comments`, `free-internal-continuation-control`, `fixed-internal-continuation-control`, `nested-internal-continuation-control`.

**Oracle:** Three boundary pairs use free form, fixed form, and a nested free include. The negative
starts the included statement with a continuation of value = 10 begun in the host;
leading comments and blank records precede that included continuation. Straight text
splicing would yield the valid value 12, so missing tokens or unrelated program syntax
are not the oracle. The diagnose location is the actual continuation record in
payload.inc or inner.inc. Each repair moves the initial host statement record into the
included text immediately before its continuation, leaving the arithmetic and other
source tokens unchanged, and checks 12.

**Oracle limitation:** The free inward-join witness also exposes p4's statement-position condition; that
tightly coupled INCLUDE boundary is explicit, not attributed to an unrelated feature. A
report on the host INCLUDE rather than the offending included record remains a location
difference. Baseline reference parsing of .inc locations is missing; keep the exact
source/line predicate and record the raw report rather than silently relocating the
fixture. A positive repair demonstrates legal internal continuation, not detection of
the negative.

**Dependencies:** 6.3.2.3/6.3.3.2 identify comment and blank records. 6.3.2.4 supplies the free
ampersands; 6.3.3.3 supplies the fixed column-six marker. 6.4 p5 requires nested
resolution before applying the boundary. 4.2 p2(5), PDF 46, supplies reporting
capability without imposing a fatal exit.

### S6.4-008: The last resolved included statement line cannot continue into its host

**Source:** 6.4 p6, last boundary condition; J3/24-007, 18 December 2023, PDF page 74, printed page 60, lines 1-2. **Class:** Restriction.

**Definition:** After INCLUDE resolution, the last included statement line is not continued beyond that
included text. Trailing comments do not hide a continued last statement, and nested
replacement does not remove the boundary condition. An ampersand in an actual trailing
comment is not continuation of either the statement or the INCLUDE line.

**Diagnostic obligation:** required.

**Facets:** `free-last-continuation-diagnostic`, `fixed-last-continuation-diagnostic`, `nested-last-continuation-diagnostic`, `trailing-comments`, `free-contained-statement-control`, `fixed-contained-statement-control`, `nested-contained-statement-control`, `comment-ampersand-control`.

**Oracle:** Three pairs place the start of value = 10 + 2 in an included asset but its completing
continuation record in the host, in free, fixed, and nested free forms. Comment records
follow the included statement. The fully spliced expression is valid; the specific
defect is crossing the include boundary. Diagnose names that last statement record in
payload.inc or inner.inc. Each repair moves only the completing host record into the
included asset before its trailing comments and checks 12. Another control ends an
otherwise complete included assignment with a comment containing ampersand and follows
it with a comment line ending in ampersand; value remains 23.

**Oracle limitation:** Fixed-form continuation is signaled on the successor record, so a processor can report
that host location instead of the included statement that has been continued. This
attribution difference must be preserved, not silently reclassified as matching the
declared included-file predicate. No EOF coordinate is invented and no whole-program
recovery span is accepted. Genuine .inc locations are presently outside the baseline
reference parser; unlocated GNU warnings cannot use the single-source exception because
these fixtures have INCLUDE and multiple inputs.

**Dependencies:** 6.3.2.4 and 6.3.3.3 define the two continuation mechanisms; the commentary and
termination subclauses distinguish a real source marker from one in a comment. 6.4 p5
supplies nested resolution. 4.2 p2(5), PDF 46, requires a reporting capability, not
compulsory fatal rejection.

<!-- END GENERATED 6.4 -->
