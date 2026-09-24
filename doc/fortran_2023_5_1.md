# Fortran 2023: 5.1 High level syntax

Source-only draft catalogue: see `doc/catalogues/high_level_syntax_5_1.json`.
No Fortran test program, execution, oracle approval, fixture approval, or coverage claim is supplied.

<!-- BEGIN GENERATED 5.1 -->

### R501: A program is a sequence of one or more program units

**Source:** R501, J3/24-007, 18 December 2023, physical PDF53. **Class:** Syntax.

**Definition:** A program consists of one program-unit followed by zero or more additional
program-units.

**Diagnostic obligation:** required.

**Facets:** `single-program-unit`, `multiple-program-units`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed: program_units_14.json, main_program_14_1.json,
module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json cover detailed program-unit bodies. This catalogue
supplies the top-level R501 sequence plans; program_concept_5_2_2.json supplies
exactly-one-main-program plans.

### R502: A program unit is one of the five top-level program-unit forms

**Source:** R502, J3/24-007, 18 December 2023, physical PDF53. **Class:** Syntax.

**Definition:** A program-unit is a main-program, external-subprogram, module, submodule, or block-data
program unit.

**Diagnostic obligation:** required.

**Facets:** `main-program-alternative`, `external-subprogram-alternative`, `module-alternative`, `submodule-alternative`, `block-data-alternative`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed: main_program_14_1.json,
module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json cover the detailed alternatives. This catalogue
supplies R502 overview admission plans.

### R503: An external subprogram is a function subprogram or subroutine subprogram

**Source:** R503, J3/24-007, 18 December 2023, physical PDF53. **Class:** Syntax.

**Definition:** An external-subprogram is either a function-subprogram or a subroutine-subprogram; the
displayed body productions are cross-references to inspected owner catalogues
function_subprogram_15_6_2_2.json, subroutine_subprogram_15_6_2_3.json,
module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json, and
block_data_program_units_14_3.json.

**Diagnostic obligation:** required.

**Facets:** `function-subprogram-alternative`, `subroutine-subprogram-alternative`, `body-productions-cross-reference`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed: function_subprogram_15_6_2_2.json covers R1532,
subroutine_subprogram_15_6_2_3.json covers R1537,
module_syntax_and_semantics_14_2_1.json covers R1404, submodules_14_2_3.json covers
R1416, block_data_program_units_14_3.json covers R1420, and
separate_module_procedures_15_6_2_5.json covers R1541.

### R504: A specification part orders USE, IMPORT, implicit, and declaration constructs

**Source:** R504, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** A specification-part has USE statements, then IMPORT statements, then an implicit part,
then declaration constructs.

**Diagnostic obligation:** required.

**Facets:** `use-before-import-before-implicit`, `declarations-after-implicit`, `late-use-rejected`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed: use_statement_and_use_association_14_2_2.json
covers USE, import_statement_8_8.json covers IMPORT, implicit_statement_8_7.json covers
IMPLICIT, and statement_order_5_3_2.json records Table 5.1 ordering. This catalogue
supplies the overview ordering controls.

### R505: An implicit part consists of optional implicit-part statements followed by an IMPLICIT statement

**Source:** R505, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** An implicit-part is zero or more implicit-part-stmts followed by an implicit-stmt.

**Diagnostic obligation:** required.

**Facets:** `parameter-before-implicit`, `format-before-implicit`, `final-implicit-statement`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogue confirmed: implicit_statement_8_7.json covers the detailed
IMPLICIT statement content. This catalogue supplies the implicit-part sequencing plans.

### R506: Implicit-part statements are IMPLICIT, PARAMETER, FORMAT, or ENTRY statements

**Source:** R506, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** An implicit-part-stmt is an implicit-stmt, parameter-stmt, format-stmt, or entry-stmt.

**Diagnostic obligation:** required.

**Facets:** `implicit-stmt-alternative`, `parameter-stmt-alternative`, `format-stmt-alternative`, `entry-stmt-alternative`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed: implicit_statement_8_7.json,
parameter_statement_8_6_11.json, format_statement_13_2_1.json, and
entry_statement_15_6_2_6.json cover the listed statement forms.

### R507: Declaration constructs include specification constructs plus DATA, FORMAT, ENTRY, and statement functions

**Source:** R507, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** A declaration-construct is a specification-construct, DATA statement, FORMAT statement,
ENTRY statement, or statement-function statement.

**Diagnostic obligation:** required.

**Facets:** `specification-construct-alternative`, `data-stmt-alternative`, `format-stmt-alternative`, `entry-stmt-alternative`, `stmt-function-alternative`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed: data_statement_8_6_7.json,
format_statement_13_2_1.json, entry_statement_15_6_2_6.json, and
statement_function_15_6_4.json cover the detailed non-specification alternatives; this
catalogue covers their R507 declaration-construct admission.

### R508: Specification constructs cover derived types, enums, interfaces, generics, parameters, procedure declarations, other specifications, and type declarations

**Source:** R508, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** A specification-construct is one of the listed type, enum, generic, interface,
parameter, procedure-declaration, other-specification, or type-declaration constructs.

**Diagnostic obligation:** required.

**Facets:** `derived-type-def-alternative`, `enum-def-alternative`, `enumeration-type-def-alternative`, `generic-and-interface-alternatives`, `declaration-statement-alternatives`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed for detailed alternatives include
enum_type_7_6_1.json, enumeration_type_7_6_2.json, interface_block_15_4_3_2.json,
generic_statement_15_4_3_3.json, parameter_statement_8_6_11.json,
procedure_declaration_statement_15_4_3_6.json, type_declaration_statements_8_2.json, and
type_declaration_7_3_2_2.json.

### R509: An execution part starts with an executable construct and may continue with execution-part constructs

**Source:** R509, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** An execution-part is an executable-construct followed by zero or more
execution-part-constructs.

**Diagnostic obligation:** required.

**Facets:** `first-executable-construct`, `following-execution-part-constructs`, `declaration-after-executable-rejected`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** statement_order_5_3_2.json records the same declaration/execution boundary; this
catalogue supplies the R509 execution-part syntax controls.

### R510: Execution-part constructs are executable constructs plus FORMAT, ENTRY, or DATA statements

**Source:** R510, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** An execution-part-construct is an executable-construct, FORMAT statement, ENTRY
statement, or DATA statement.

**Diagnostic obligation:** required.

**Facets:** `executable-construct-alternative`, `format-after-executable-admitted`, `data-after-executable-admitted`, `entry-after-executable-source-control`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed: format_statement_13_2_1.json,
entry_statement_15_6_2_6.json, and data_statement_8_6_7.json cover detailed statement
semantics; this catalogue owns their R510 admission among execution-part constructs.

### R511: An internal subprogram part starts with CONTAINS and then internal subprograms

**Source:** R511, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** An internal-subprogram-part is a CONTAINS statement followed by zero or more
internal-subprograms.

**Diagnostic obligation:** required.

**Facets:** `contains-before-internal-subprogram`, `zero-or-more-internal-subprograms`, `missing-contains-rejected`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogue confirmed: contains_statement_15_6_2_8.json covers CONTAINS;
statement_order_5_3_2.json repeats the common ordering relation. This catalogue supplies
R511 internal-subprogram-part plans.

### R512: Internal subprograms are function or subroutine subprograms

**Source:** R512, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** An internal-subprogram is a function-subprogram or subroutine-subprogram; the displayed
module-subprogram productions are cross-references to
module_syntax_and_semantics_14_2_1.json and separate_module_procedures_15_6_2_5.json.

**Diagnostic obligation:** required.

**Facets:** `internal-function-subprogram`, `internal-subroutine-subprogram`, `module-subprogram-cross-reference`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed: function_subprogram_15_6_2_2.json,
subroutine_subprogram_15_6_2_3.json, module_syntax_and_semantics_14_2_1.json, and
separate_module_procedures_15_6_2_5.json cover the displayed subprogram alternatives.

### R513: Other specification statements are the listed attributes and storage-association statements

**Source:** R513, J3/24-007, 18 December 2023, physical PDF54. **Class:** Syntax.

**Definition:** An other-specification-stmt is one of the listed access, attribute, binding, procedure,
namelist, common, or equivalence statements.

**Diagnostic obligation:** required.

**Facets:** `attribute-statement-alternatives`, `procedure-and-binding-alternatives`, `storage-association-alternatives`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
High-level Clause 5 grammar entries cross-reference inspected owner catalogues
main_program_14_1.json, module_syntax_and_semantics_14_2_1.json, submodules_14_2_3.json,
block_data_program_units_14_3.json, function_subprogram_15_6_2_2.json, and
subroutine_subprogram_15_6_2_3.json for full program-unit and procedure bodies;
duplicate fixture binding is deferred to those owners.

**Dependencies:** Existing owner catalogues confirmed for representative listed statements include
accessibility_statement_8_6_1.json, external_statement_15_4_3_5.json,
intrinsic_statement_15_4_3_7.json, procedure_declaration_statement_15_4_3_6.json,
common_statement_8_10_2_1.json, and equivalence_statement_8_10_1_1.json; this catalogue
supplies the R513 overview admission plans.

### R515: Action statements are the listed executable statement forms

**Source:** R515, J3/24-007, 18 December 2023, physical PDF55. **Class:** Syntax.

**Definition:** An action-stmt is one of the listed action statement forms; this catalogue registers
bare action statements used directly as executable constructs in an execution part,
while detailed statement semantics remain with their owner catalogues.

**Diagnostic obligation:** required.

**Facets:** `bare-assignment-action-stmt`, `bare-call-action-stmt`, `bare-io-action-stmt-family`, `bare-allocation-pointer-action-stmt-family`, `bare-control-action-stmt-family`, `image-team-action-stmt-family`.

**Oracle:** Future syntax fixtures use complete source files plus valid controls that repair only
the named grammar relation; diagnostics need no fixed wording, severity, status, or
printed rule number.

**Oracle limitation:** Source accounting only. This packet creates no Fortran fixture, compiler invocation,
execution evidence, evidence link, fixture approval, oracle approval, or coverage claim.
Bare-action controls prove R515 admission only when the action statement appears
directly in an execution part; detailed statement effects, I/O semantics, branch target
constraints, and coarray/team runtime behavior remain with their owner catalogues.

**Dependencies:** R514 remains deferred to existing tests/reviews.json entries
S7_5_6_3_005_valid__final_event_do_result and S7_5_6_3_005_valid__final_event_if_result,
whose discriminating constructs are DO and block IF executable constructs. R515 is
registered locally because those sources do not discriminate a bare action-stmt directly
in an execution part. Detailed owners include
general_form_of_assignment_statement_10_2_1_1.json,
syntax_of_a_procedure_reference_15_5_1.json, Clause 12 I/O statement catalogues, and
statement_order_5_3_2.json.

<!-- END GENERATED 5.1 -->
