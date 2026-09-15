! rule: S7.4.3.2-006
! covers: d-exponent-double
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    if (kind(0.0D0) /= kind(0.0d0)) error stop 1
    call check(0.0D0)
    if (kind(0d0) /= kind(0.0d0)) error stop 2
    call check(0d0)
contains
    subroutine check(value)
        real(kind(0.0d0)), intent(in) :: value
        if (kind(value) /= kind(0.0d0)) error stop 20
    end subroutine
end program numeric_literal_case
