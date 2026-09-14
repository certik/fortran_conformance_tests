! rule: S7.4.3.1-006
! covers: omitted-default
! evidence: effect
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: destination
    destination = 37
    if (kind(37) /= kind(0)) error stop 1
    if (destination /= 30_k + 7_k) error stop 2
end program
