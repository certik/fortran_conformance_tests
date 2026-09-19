# Fortran 2023 9.3: Constant

The canonical catalogue is `doc/catalogues/constant_9_3.json`. Effective review state comes from
`Registry.catalogue_review_state("9.3")`; source accounting does not
approve cases, canonical relationships or an execution inventory.

Authority: original J3/24-007, 18 December 2023, 688 pages, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.

One base unit, p1. This source-only packet records literal and named constants, PARAMETER dependencies, always-permitted references, and the prohibition on redefinition without approving any fixture.

All facets in this packet are pending source plans. No Fortran test program,
compiler invocation, execution evidence, oracle approval, fixture approval or
coverage claim is supplied here.

<!-- BEGIN GENERATED 9.3 -->

### S9.3-001: Constants are literal or named and may be referenced but not redefined

**Source:** 9.3 p1, J3/24-007, 18 December 2023, physical PDF151. **Class:** Restriction.

**Definition:** A constant, as cross-referenced to 6.2.3, is a literal constant or a named constant. A
literal constant is a scalar syntactic form indicating type, type parameters and value.
A named constant is a constant with a name that has the PARAMETER attribute under 8.5.13
or 8.6.11. A reference to a constant is always permitted, and redefinition of a constant
is never permitted.

**Diagnostic obligation:** not-required.

**Facets:** `literal-constant-reference`, `named-constant-reference`, `parameter-attribute-source`, `constant-subobject-reference`, `constant-redefinition-prohibited`.

**Oracle:** Source-qualified paired plans and positive-control admissions, with any future
executable observation delegated to the owning semantic requirement. A literal expected
value or fixed inquiry result is stated only where the future program first establishes
definedness and execution of the relevant path.

**Oracle limitation:** The permission to reference a constant is not a claim that every occurrence is valid in
every syntactic context, and the redefinition prohibition is not treated as an automatic
numbered-constraint-style diagnostic duty here. All entries are PENDING plans only; no
case, execution, oracle, source-use link, fixture approval or coverage claim is created.

**Dependencies:** 6.2.3R604-R607/C602;8.5.13p1-p2/C852-C853;8.6.11R854-R855/p1-p4;9.2C901;10.1.12;19.6.5.

<!-- END GENERATED 9.3 -->
