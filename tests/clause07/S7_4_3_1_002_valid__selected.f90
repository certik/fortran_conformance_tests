! rule: S7.4.3.1-002
! covers: selected-zero selected-signed-zero
! evidence: effect
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: bare, positive, negative
    data bare, positive, negative /0_k, +0_k, -0_k/
    if (bare /= 1_k - 1_k) error stop 1
    if (positive /= 1_k - 1_k) error stop 2
    if (negative /= 1_k - 1_k) error stop 3
    if (bare < 0_k) error stop 4
    if (bare > 0_k) error stop 5
    if (positive < 0_k) error stop 6
    if (positive > 0_k) error stop 7
    if (negative < 0_k) error stop 8
    if (negative > 0_k) error stop 9
end program
