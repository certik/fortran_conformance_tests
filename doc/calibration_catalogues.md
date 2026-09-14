# Additional catalogue and fixture calibrations

These are deliberately partial catalogues. The generic source census lists
the entire corresponding subclauses, and unresolved passages remain visible.
Definitions below are generated from `doc/catalogues/`; do not edit the
generated regions by hand.

## Fixed-form continuation

The fixture uses actual fixed-form column positions, CRLF records, and no
in-band test directives. Its bytes are copied and hashed before compilation.
Only the continuation behavior in the mapped source passage is claimed;
other source-form restrictions are not silently marked covered.

<!-- BEGIN GENERATED 6.3.3.3 -->

### S6.3.3.3-001: Fixed-form continuation uses character position six

**Source:** 6.3.3.3 p1. **Class:** Effect.

**Definition:** A fixed-form continuation indicator in position six causes the statement field on that
line to extend the preceding noncomment statement. Blank and zero instead indicate an
initial line.

**Diagnostic obligation:** required.

**Facets:** `numeric-indicator`, `punctuation-indicator`.

**Oracle:** Compile the byte-preserved fixed-form fixture. Numeric and exclamation-mark continuation
indicators must produce independently known expression values. External stdout checks
observe those values; staging hashes establish that the harness did not rewrite columns
or line endings.

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
