! rule: S7.4.3.1-005
! covers: selected-small-boundary
! evidence: effect
! profile: integer-literal-range4-binary15
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(4)
    integer(k) :: upper, adjacent, positive, lower
    data upper /32767_k/
    data adjacent /32766_k/
    data positive /+32767_k/
    data lower /-32767_k/
    if (upper /= huge(upper)) error stop 1
    if (adjacent /= huge(adjacent) - 1_k) error stop 2
    if (positive /= huge(positive)) error stop 3
    if (lower /= -huge(lower)) error stop 4
end program
