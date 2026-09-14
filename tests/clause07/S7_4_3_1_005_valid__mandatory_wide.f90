! rule: S7.4.3.1-005
! covers: eighteen-digit-values
! evidence: effect
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: positive, negative, expected
    integer :: i
    data positive, negative /+999999999999999999_k, -999999999999999999_k/
    expected = 0_k
    do i = 1, 18
        if (expected > (huge(expected) - 9_k) / 10_k) error stop 1
        expected = 10_k * expected + 9_k
    end do
    if (positive /= expected) error stop 2
    if (negative /= -expected) error stop 3
end program
