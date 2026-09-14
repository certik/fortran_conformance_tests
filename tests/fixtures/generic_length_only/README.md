# C1514: LEN-only generic ambiguity (draft)

The pin is J3/24-007, dated 2023-12-18, SHA-256
`7371e889f231cfb0316d30365d5083fb5af34cbb6d5f7cb1e01855c73021bfa2`.
The original 7.2 p2 is on PDF76 (printed 62). The full 15.4.3.4.5 text
starts on PDF331 and continues through p5/NOTE 2 on PDF332 (printed
317-318). Its inventory page is a start, not the entire C1514 text.

Both module specifics have explicit interfaces under 15.4.2.1 p1. The
generic block names each once and meets R1501/R1506/R1508 and
C1504/C1507-C1509 (PDF325-327). It is an ordinary generic name, not an
operator, assignment, defined I/O or intrinsic extension. The remaining
distinction must therefore meet C1514, not C1511-C1513.

Each specific has one nonoptional, non-passed-object scalar CHARACTER
dummy, named `value`, in position one, with the same default kind and
INTENT(IN). They differ only in LEN. Under p2/p3 they remain mutually TKR
compatible and not distinguishable. The C1514 alternatives fail: (1) one
does not exceed one; (2) zero does not exceed zero; (3) neither has a passed
object; (4) neither position nor name distinguishes the dummies.

The sibling `generic_length_rank_control` changes only `value` to
`value(1)` in the second declaration. The differing ranks make the
data dummies mutually non-TKR-compatible, satisfying (1) and (4).
Both fixtures stop at compilation. There is no invocation, argument
association error, assumed optional kind, or claimed runtime dispatch.

The declared diagnostic relation is lines 3-11: the generic declaration,
both specific signatures and both dummy declarations. GNU reports its
ambiguity at a specific signature; Flang at the generic declaration.
A causal ambiguity/distinguishability message is required. A whole-module
range (lines 1-13), unlocated summary, unsupported-feature report or
crash/verifier/resource failure cannot satisfy this relation. `diagnose`
observes reporting, not compulsory fatal rejection, consistently with
4.2 p2(3), PDF46. The message substrings are fixture predicates, not
standard-mandated wording.

`doc/evidence/canonical_case_links.json` links these exact canonical IDs
to `S7.2-003/length-only-overload-exclusion`. That independent source
adjudication is not created by successful compiles or a failing negative.
The fixture reviews and the link are initially unreviewed; the link does
not ratify the whole generic-declaration subclause.
