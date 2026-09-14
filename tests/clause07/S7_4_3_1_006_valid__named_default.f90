! rule: S7.4.3.1-006
! covers: named-default
! evidence: effect
program p
    implicit none
    integer, parameter :: k = kind(0)
    if (kind(37_k) /= k) error stop 1
    call check(37_k)
contains
    subroutine check(value)
        integer(k), intent(in) :: value
        if (value /= 30_k + 7_k) error stop 2
    end subroutine
end program
