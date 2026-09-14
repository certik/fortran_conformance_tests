# Fortran 2023: 7.2 Type parameters

Draft source catalogue: `doc/catalogues/type_parameters.json`.
Pinned J3/24-007, 18 December 2023: PDF 76, printed 62, paragraphs 1-7,
R701/C701/C702 and notes 1-2, numbered lines 4-25.

Syntax controls, restrictions, parameter properties, generic resolution,
deferred effects and assumed-length effects have separate evidence.
R701/C701/C702 retain their official ownership. All six invalid fixtures
use compile-only `diagnose` contracts with a declared source file/line and
minimal repaired controls, not mandatory fatal rejection or optional rule
codes. Missing PDT implementation is not an intended language diagnostic.

Kind numbers are obtained from standard inquiries, not presumed byte
widths. Default and double-precision real kinds are distinguished by the
standard's strict precision ordering. PDT kind discriminator values are
not used as intrinsic kind selectors; the explicit integer parameter-kind
case does not assume its selected kind differs from default.

The finite plan leaves twelve facets explicitly pending: two parameter
domain/use contracts, the parameter-type graph, length-only overload
exclusion, four deferred-PDT mechanisms and their use graph, two assumed-PDT
mechanisms and their use graph. The catalogue gives concrete next evidence
for each. Definition/permission/informative accounting is not a processor
pass. Source-only failed implementations, authoring coverage and independent
review remain separate; this batch does not close the whole standard.

<!-- BEGIN GENERATED 7.2 -->

### R701: Type-parameter values have expression, asterisk and colon forms

**Source:** 7.2 R701, PDF 76, printed 62, lines 12-14. **Class:** Syntax.

**Definition:** A type-param-value has a scalar integer expression, an asterisk, or a colon form.
Enclosing contexts and associated constraints still apply: a kind parameter requires a
constant expression, a colon needs a POINTER or ALLOCATABLE entity, and an
assumed-length asterisk needs an allowed context. Expression syntax is not itself a
requirement that a length be constant.

**Diagnostic obligation:** required.

**Facets:** `scalar-integer-expression`, `assumed-token`, `deferred-token`, `malformed-expression`.

**Oracle:** Independent positive controls use a dummy-dependent scalar length expression in a
subprogram, an assumed-length character dummy, and a deferred-length allocatable
character. A compile-only manifest isolates CHARACTER(LEN=2+) as the malformed form; its
repaired control changes only 2+ to 2+1. The diagnostic is bound to that declaration's
file and line.

**Oracle limitation:** The malformed form tests expression syntax, not noninteger type, rank, unsupported kinds
or invalid asterisk/colon placement. R403/C401 and canonical int-expr typing retain
their owners. The three form controls do not independently prove parameter
establishment, generic selection or constraint-reporting capability. A required
reporting capability is not compulsory fatal rejection; the negative uses diagnose, not
legacy reject.

**Dependencies:** 4.1.2 p2 and 4.2 p2(3) (PDF 45-46); C701/C702 and 7.2 p5-p7; 7.3.2.1/C704 (PDF 77),
7.4.4.2/R721-R723/C726 (PDF 84-85), and 10.1.11 p1-p2 (PDF 185-186). The INTENT(IN),
nonoptional scalar integer dummy is a legal specification-expression primary.

### C701: A kind type-parameter value is a constant expression

**Source:** 7.2 C701 (R701), PDF 76, printed 62, line 15. **Class:** Restriction.

**Definition:** Where a type-param-value supplies a kind parameter, it must be a constant expression. A
legal nonconstant specification expression is insufficient. Neither an assumed asterisk
nor a deferred colon supplies a constant kind value, even when the entity's
dummy/POINTER attributes satisfy the independent placement rules.

**Diagnostic obligation:** required.

**Facets:** `constant-expression`, `nonconstant-expression`, `assumed-kind`, `deferred-kind`.

**Oracle:** Three compile-only PDT pairs isolate a nonconstant INTENT(IN) integer dummy expression,
an asterisk on a dummy's kind parameter, and a colon on a pointer dummy's kind
parameter. Each minimal repair replaces only that parameter value with KIND(0). The
PDT's integer KIND parameter is an abstract discriminator and is not used as an
intrinsic representation selector. The asterisk/colon pairs give the kind parameter a
default, so treating an explicit invalid token as an omitted argument cannot produce a
misleading missing-default report. Each invalid report must be located at its offending
TYPE declaration.

**Oracle limitation:** Using INTEGER(KIND=runtime) would also enter R706's explicit scalar-int-constant-expr
grammar rather than isolate R701/C701, so these witnesses use an actual PDT
type-param-value context. The dummy-dependent expression satisfies the independent
specification-expression premise. The asterisk is in a dummy context admitted by C7100;
the colon entity is a POINTER as required by C702. Their default does not legalize an
explicitly assumed/deferred kind. Exact declaration points and source-reviewed
constancy-message predicates exclude same-line unsupported-feature reports as well as
broad recovery ranges. These observed wording predicates are not standard-mandated
diagnostic text. Unimplemented PDT diagnostics, missing-default fallbacks, earlier
errors, crashes or a failing repaired control cannot corroborate the intended violation.
Unsupported reference controls remain source-only evidence, not an excuse to rewrite the
type as an intrinsic kind. Compile success does not claim a runtime result.

**Dependencies:** 7.5.2.1/R726-R727 (PDF 88), 7.5.3.1/R732-R734/p2-p5 (PDF 91-92), 7.5.9/R754-R755/C7100
(PDF 106), 10.1.11 p1-p2 (PDF 185), 10.1.12 p1 (PDF 187-188), 16.9.118 (PDF 424). 4.2
p2(3) requires reporting capability, not a particular process exit status, severity or
rule code.

### C702: A colon type-parameter value needs POINTER or ALLOCATABLE

**Source:** 7.2 C702 (R701), PDF 76, printed 62, lines 16-17. **Class:** Restriction.

**Definition:** A colon may be used as a type-param-value only in the declaration of an entity with
POINTER or ALLOCATABLE. Either attribute suffices; it need not be spelled in the same
type-declaration statement if the entity receives it in a permitted separate attribute
statement. This exception does not allow a deferred kind, waive other declaration
constraints, or give an unallocated/disassociated object's deferred parameter a value.

**Diagnostic obligation:** required.

**Facets:** `character-allocatable`, `character-pointer`, `separate-attributes`, `pdt-allocatable`, `pdt-pointer`, `character-missing-attributes`, `pdt-missing-attributes`.

**Oracle:** Runtime character controls exercise ALLOCATABLE and POINTER independently, checking
allocation/association before LEN or payload. A compile-only control supplies the
attributes in separate statements. Two compile-only invalid/control pairs remove or add
only ALLOCATABLE for a deferred character length and a PDT LEN parameter. A further
compile-only PDT POINTER control covers the other exception. Invalid diagnostic
locations are the individual declarations.

**Oracle limitation:** All deferred parameters here are lengths. The PDT's LEN parameter is distinct from its
integer component type, so an unsupported intrinsic kind cannot be the earlier error.
The compile-only controls do not read unused, unallocated or disassociated objects. The
two negative cases isolate the missing entity attribute; no shape, allocation,
initialization or argument mismatch is introduced. Exact declaration points and
source-reviewed POINTER/ALLOCATABLE message predicates distinguish normal attribute
diagnostics from same-line unsupported-feature errors; the standard does not mandate
those particular words. Reporting is observed independently of ordinary exit status,
while verifier/crash/resource failures remain failures.

**Dependencies:** 7.2 p5-p6, 7.4.4.2 (PDF 84-85), 7.5.3.1 and 7.5.9 (PDF 91-92, 106), 8.5.3/8.5.14 (PDF
120, 131), 8.6.2 and 8.6.12 (PDF 135, 139-140), 9.4.5 p2 (PDF 153), and 4.2 p2(3). Kind
constancy remains owned by C701.

### S7.2-001: Parameter values affect value domains, denotation and operations

**Source:** 7.2 p1, PDF 76, printed 62, lines 4-5. **Class:** Effect.

**Definition:** For a parameterized type, its value set, value-denoting syntax and operations depend on
its parameter values as specified in the defining type and expression rules. This is not
a claim that every parameter change changes all three observables, nor that all kinds
have different values or increasing integer identifiers. Kind, length, type category and
rank are separate.

**Diagnostic obligation:** not-required.

**Facets:** `character-length-values`, `concatenation-length`, `literal-kind`, `operation-kind`, `parameter-use-graph`, `processor-value-set-interface`.

**Oracle:** A character program checks initialized values of lengths zero, two and four, and the
exact value/length of their concatenation. A separate real program obtains default and
double-precision kinds from KIND(0.0) and KIND(0.0D0), checks the required precision
ordering, literal suffix kinds and the kind of a mixed default/double operation. It uses
only zero-valued arithmetic.

**Oracle limitation:** Double precision is guaranteed to have greater decimal precision than default real, so
this pair does not assume optional kinds or byte-valued selectors. Equal-precision
alternative real kinds are not given an invented ordering. These observations do not
prove entire value sets or every operation. No floating tolerance, radix, signed-zero
distinction or character code is prescribed.

**Dependencies:** 7.4.3.2 p1/p4-p7 (PDF 81-82); 7.4.4.1-.2 (PDF 84-85); 10.1.5.3.1 (PDF 178); 10.1.9.3 p4
(PDF 184-185); 16.9.118 and 16.9.122 (PDF 424, 426).

### S7.2-002: Type parameters are integer and intrinsic parameter names are defined

**Source:** 7.2 p2, PDF 76 lines 6-7, and p3, lines 9-10 (printed 62). **Class:** Effect.

**Definition:** Every type parameter has integer type. Every intrinsic type has a parameter named KIND,
and character additionally has LEN. The kind of a parameter itself is not the
parameter's value: intrinsic KIND parameters have default integer kind by 7.4.1,
character LEN's integer kind is processor dependent, and PDT parameters can declare an
integer kind explicitly. A LEN parameter need not describe a physical length.

**Diagnostic obligation:** not-required.

**Facets:** `intrinsic-kind-integer-names`, `character-length-integer-name`, `pdt-integer-parameter-kinds`, `parameter-type-use-graph`.

**Oracle:** One program uses %KIND on all five intrinsic types and passes each result to an explicit
default-integer dummy, also comparing against KIND of the initialized object. A separate
character %LEN program passes that inquiry to a dummy whose integer kind is obtained
from KIND(text%LEN), without assuming it is default. A PDT program declares both its
KIND and LEN parameters with SELECTED_INT_KIND(18), checks the parameter inquiries'
kinds and integer values, then safely initializes and checks a small component array.

**Oracle limitation:** KIND/LEN intrinsics provide comparison values but are not substitutes for checking the
parameter names. The PDT kind discriminator is not an intrinsic representation selector.
F2023 requires an integer method of range at least 18, but that method need not be
nondefault; the PDT case is marked F2023 and its original runtime oracle is retained if
a reference lacks support. An integer assignment conversion alone would not establish an
inquiry's type, so the controls use explicit typed procedure arguments.

**Dependencies:** 7.4.1 p2 (PDF 80), 7.4.3.1 p2/p4 (PDF 80), 7.4.4.1 p1 (PDF 84), 7.5.3.1 p2-p5 (PDF 92),
7.5.9 p2 (PDF 106), 9.4.5 (PDF 153-154), 10.1.9.2 p1 (PDF 184), 16.9.118 (PDF 424). The
positive call premises follow 15.5.2.5; no legacy clause15 file or shared profile is
changed.

### S7.2-003: Kind participates in generic resolution but length does not

**Source:** 7.2 p2, PDF 76, printed 62, lines 7-8. **Class:** Effect.

**Definition:** Generic resolution uses corresponding kind parameters but not length parameters. Type
category, kind and rank distinguishability remain separate, and the generic declaration
rules and other argument characteristics still apply. Different character lengths alone
do not distinguish otherwise identical specific procedures.

**Diagnostic obligation:** context-dependent.

**Facets:** `real-kind-selection`, `character-length-invariance`, `pdt-kind-and-length-selection`, `length-only-overload-exclusion`.

**Oracle:** A same-rank real generic dispatches default and double-precision actuals to different
integer tags; these two kinds are guaranteed distinct by precision, not numeric kind
codes. A character generic with one assumed-length specific is invoked with two lengths
and returns/checks the actual lengths. A PDT generic uses kind discriminators 1 and 2
with assumed LEN, varies LEN while holding KIND fixed, then varies KIND while holding
LEN fixed; tags and parameter inquiries are checked. The length-only-overload-exclusion
facet has authored finite linkage S7.2-003.length-only-overload-exclusion in
doc/evidence/canonical_case_links.json: C1514_invalid__length_only is paired with the
compile-only C1514_valid__length_rank_control. Both retain primary ownership C1514; no
supplementary rejection execution is added.

**Oracle limitation:** The PDT discriminator values 1 and 2 have no role as intrinsic kind selectors; their
integer component uses the default integer type. They may therefore be used without a
representation profile. The direct same-specific controls do not establish forbidden
length-only overloading. The linked scalar-character pair differs only in LEN; adding
rank one to the second dummy repairs distinguishability. No calls introduce competing
length/rank errors. A causal ambiguity/distinguishability report must fit the declared
generic/signature relation, not a whole-module recovery span. Authored linkage clears
only the authoring gap: normal audit still requires independent current source, fixture
and link reviews. The link is neither a runtime effect nor a derived passing aggregate,
and does not ratify all of 15.4.3.4.5, all parameter contexts, or the broader
meta-evidence work. Valid PDT reference failures remain implementation/source-only
findings, not justification to drop LEN or collapse the generic.

**Dependencies:** 7.4.3.2 p5 (PDF 82), 7.5.3.1 (PDF 91-92), 7.5.9/C7100 (PDF 106), 15.4.3.4.5 p1-p3/C1514
(PDF 331-332), 15.5.5.2 (PDF 350-351). TKR compatibility explicitly excludes length;
generic eligibility is not tested with legacy argument-kind negatives.

### S7.2-004: Execution establishes deferred type-parameter values

**Source:** 7.2 p6, PDF 76, printed 62, lines 19-21; explanatory NOTE 1 immediately follows. **Class:** Effect.

**Definition:** Deferred parameters of an object acquire values through successful ALLOCATE execution,
intrinsic assignment, pointer assignment or argument association, according to the
respective canonical rules. A declaration with colon alone does not establish a value.
Allocation failure, an unallocated allocatable or a disassociated/undefined pointer does
not license inquiry of a deferred parameter. The mechanism does not turn kind parameters
into deferred parameters.

**Diagnostic obligation:** not-required.

**Facets:** `allocate-character`, `intrinsic-assignment-character`, `pointer-assignment-character`, `allocatable-argument-character`, `pointer-argument-character`, `allocate-pdt`, `intrinsic-assignment-pdt`, `pointer-assignment-pdt`, `argument-association-pdt`, `deferred-parameter-use-graph`.

**Oracle:** Five independent character programs establish deferred length by explicit allocation of
a small array, repeated intrinsic assignment with changing scalar lengths, pointer
reassociation to live defined targets, allocatable dummy association and pointer dummy
association. Each dynamic-state check is a separate statement before LEN, SIZE,
association-with-target checks or payload access. The allocated array is shape-checked
before element initialization and reads.

**Oracle limitation:** All five executed routes use supported default character kind and preserve the different
allocation/association requirements. They do not prove PDT behavior, procedure result
descriptors or universal deferred-parameter semantics. No short-circuit boolean
expression is used to guard an unsafe inquiry. Character scalar-to-array allocation is
not invented: explicit shape allocation precedes array-section assignment.

**Dependencies:** 9.4.5 p2 (PDF 153); 9.7.1.1 p5-p6/C936-C940 and 9.7.1.2-.3 (PDF 160-163); 10.2.1.3 p3
(PDF 190); 8.5.14 p2-p3 (PDF 131), 10.2.2.2-.3 (PDF 194-195); 15.5.2.6-.8 (PDF 342-343).
The assignment catalogue's canonical requirements remain unchanged and are not
automatically credited.

### S7.2-005: Assumed length parameters take values from their specified source

**Source:** 7.2 p7, PDF 76, printed 62, lines 22-25. **Class:** Effect.

**Definition:** An asterisk denotes an assumed length parameter. A dummy obtains it from its effective
argument; a SELECT TYPE associate name obtains it from the corresponding selector; a
named character constant obtains its length from the defining constant expression. These
uses do not assume a kind parameter or defer the length for allocation. Context
restrictions in the defining type-specifier rules still apply.

**Diagnostic obligation:** not-required.

**Facets:** `dummy-character`, `select-type-character`, `named-character-constant`, `dummy-pdt`, `select-type-pdt`, `assumed-parameter-use-graph`.

**Oracle:** Separate programs check a character dummy at two actual lengths, an
unlimited-polymorphic dummy selected through TYPE IS(CHARACTER(LEN=*)) at two lengths,
and character PARAMETER constants whose expressions include concatenation, trailing
blanks and an empty string. Expected lengths are literal small counts, not LEN of the
same tested object.

**Oracle limitation:** SELECT TYPE uses initialized ordinary arguments, an explicit class-default failure
branch and no unchecked dynamic data. Named constants satisfy constant-expression and
prior-definition rules. The three character controls do not establish PDT or every
asterisk context. KIND is obtained from standard default-character premises, never
hard-coded as 1.

**Dependencies:** 7.4.4.2/C726-C728/p5 (PDF 84-85), 7.5.9/C7100 (PDF 106), 8.5.13 (PDF 130-131), 10.1.12
(PDF 187-188), 11.1.11.1/C1164-C1165 and 11.1.11.2 p3/p5 (PDF 225-226), 15.5.2.5 p3-p5
(PDF 340).

<!-- END GENERATED 7.2 -->
