! rule: S7.4.5-002
! covers: one-method-minimum
! evidence: effect
! standard: f2023
program numeric_literal_case
    use iso_fortran_env, only: logical_kinds
    implicit none
    if (size(logical_kinds) < 1) error stop 1
    if (.not. any(logical_kinds == kind(.false.))) error stop 2
    if (.not. any(logical_kinds == kind(.true.))) error stop 3
end program numeric_literal_case
