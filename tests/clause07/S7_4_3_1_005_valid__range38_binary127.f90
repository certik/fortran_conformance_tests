! rule: S7.4.3.1-005
! covers: optional-large-boundary
! evidence: effect
! profile: integer-literal-range38-binary127
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(38)
    integer(k) :: upper, adjacent, positive, lower
    data upper /170141183460469231731687303715884105727_k/
    data adjacent /170141183460469231731687303715884105726_k/
    data positive /+170141183460469231731687303715884105727_k/
    data lower /-170141183460469231731687303715884105727_k/
    if (upper /= huge(upper)) error stop 1
    if (adjacent /= huge(adjacent) - 1_k) error stop 2
    if (positive /= huge(positive)) error stop 3
    if (lower /= -huge(lower)) error stop 4
end program
