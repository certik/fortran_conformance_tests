# Fortran 2023 9.1: Designator

The canonical catalogue is `doc/catalogues/designator_9_1.json`. Effective review state comes from
`Registry.catalogue_review_state("9.1")`; source accounting does not
approve cases, canonical relationships or an execution inventory.

Authority: original J3/24-007, 18 December 2023, 688 pages, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.

Two base units: R901 and p1. This source-only packet accounts for the seven designator alternatives without taking ownership of their detailed 9.4/9.5 definitions, and records the reference terminology as definitional.

All facets in this packet are pending source plans. No Fortran test program,
compiler invocation, execution evidence, oracle approval, fixture approval or
coverage claim is supplied here.

<!-- BEGIN GENERATED 9.1 -->

### R901: A designator is one of the seven designator forms

**Source:** 9.1 R901, J3/24-007, 18 December 2023, physical PDF150. **Class:** Syntax.

**Definition:** A designator is exactly one of: object-name, array-element, array-section,
coindexed-named-object, complex-part-designator, structure-component, or substring. The
detailed formation and semantic restrictions for those alternatives are supplied by
their owning subclauses; this rule does not define array, component, coindexing,
complex-part, or substring semantics itself.

**Diagnostic obligation:** required.

**Facets:** `object-name-alternative`, `array-element-alternative`, `array-section-alternative`, `coindexed-named-object-alternative`, `complex-part-designator-alternative`, `structure-component-alternative`, `substring-alternative`.

**Oracle:** Source-qualified paired plans and positive-control admissions, with any future
executable observation delegated to the owning semantic requirement. A literal expected
value or fixed inquiry result is stated only where the future program first establishes
definedness and execution of the relevant path.

**Oracle limitation:** This catalogue records source requirements and plans only. It does not approve a Fortran
fixture, run a processor, create coverage, or transfer ownership from the cited
subclauses. Any later reuse must re-check all prerequisites, repairs, modes and
overlapping constraints.

**Dependencies:** 4.2;6.2.2;9.2R903/C903/p2;9.4.1R908-R910/C908/p2-p3;9.4.2R911-R913/C909-C920/p1-p6;9.4.3R914/C921/p1;9.4.4R915/C922/p1;9.5.3.1R917-R925/C924-C931/p1-p2;9.5.3.2;9.5.3.3;19.6.5;19.6.6.

<!-- END GENERATED 9.1 -->
