! rule: S7.4.3.1-003
! covers: method-exists eighteen-digit-capacity
! evidence: effect
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: value
    integer :: i
    if (k < 0) error stop 1
    value = 0_k
    do i = 1, 18
        if (value > (huge(value) - 9_k) / 10_k) error stop 2
        value = value * 10_k + 9_k
    end do
    do i = 1, 18
        if (mod(value, 10_k) /= 9_k) error stop 3
        value = value / 10_k
    end do
    if (value /= 0_k) error stop 4
end program
