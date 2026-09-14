! rule: S7.4.3.1-005
! covers: selected-wide-boundary
! evidence: effect
! profile: integer-literal-range18-binary63
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: upper, adjacent, positive, lower
    data upper /9223372036854775807_k/
    data adjacent /9223372036854775806_k/
    data positive /+9223372036854775807_k/
    data lower /-9223372036854775807_k/
    if (upper /= huge(upper)) error stop 1
    if (adjacent /= huge(adjacent) - 1_k) error stop 2
    if (positive /= huge(positive)) error stop 3
    if (lower /= -huge(lower)) error stop 4
end program
