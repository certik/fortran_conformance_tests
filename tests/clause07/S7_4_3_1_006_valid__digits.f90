! rule: S7.4.3.1-006
! covers: numeric-selector
! evidence: effect
! profile: integer-literal-kind-eight
program p
    implicit none
    integer, parameter :: k = 8
    if (kind(37_8) /= k) error stop 1
    call check(37_8)
contains
    subroutine check(value)
        integer(k), intent(in) :: value
        if (value /= 30_k + 7_k) error stop 2
    end subroutine
end program
