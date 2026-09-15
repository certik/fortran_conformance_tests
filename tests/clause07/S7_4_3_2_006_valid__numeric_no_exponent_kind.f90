! rule: S7.4.3.2-006
! covers: no-exponent-default
! evidence: effect
! standard: f2023
program numeric_literal_case
    implicit none
    if (kind(0.0) /= kind(0.0)) error stop 1
    call check(0.0)
    if (kind(0.) /= kind(0.0)) error stop 2
    call check(0.)
    if (kind(.0) /= kind(0.0)) error stop 3
    call check(.0)
contains
    subroutine check(value)
        real(kind(0.0)), intent(in) :: value
        if (kind(value) /= kind(0.0)) error stop 20
    end subroutine
end program numeric_literal_case
