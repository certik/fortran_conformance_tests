! rule: S7.4.3.2-001
! covers: two-method-minimum default-double-membership
! evidence: effect
! standard: f2023
program numeric_literal_case
    use iso_fortran_env, only: real_kinds
    implicit none
    real :: r = 0.0
    double precision :: d = 0.0d0
    if (size(real_kinds) < 2) error stop 1
    if (kind(r) /= kind(0.0)) error stop 2
    if (kind(d) /= kind(0.0d0)) error stop 3
    if (kind(r) == kind(d)) error stop 4
    if (.not. any(real_kinds == kind(r))) error stop 5
    if (.not. any(real_kinds == kind(d))) error stop 6
end program numeric_literal_case
