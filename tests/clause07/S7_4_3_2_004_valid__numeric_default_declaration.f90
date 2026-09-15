! rule: S7.4.3.2-004
! covers: default-declaration-kind
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    real :: value = 0.0
    if (kind(value) /= kind(0.0)) error stop 1
    call check(value)
contains
    subroutine check(x)
        real(kind(0.0)), intent(in) :: x
        if (kind(x) /= kind(0.0)) error stop 2
        if (x /= 0.0) error stop 3
    end subroutine
end program numeric_literal_case
