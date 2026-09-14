! rule: S7.4.3.1-005
! covers: default-model-boundary
! evidence: effect
! profile: integer-literal-default-binary31
! standard: f2023
program p
    implicit none
    integer :: upper, adjacent, positive, lower
    data upper /2147483647/
    data adjacent /2147483646/
    data positive /+2147483647/
    data lower /-2147483647/
    if (upper /= huge(upper)) error stop 1
    if (adjacent /= huge(adjacent) - 1) error stop 2
    if (positive /= huge(positive)) error stop 3
    if (lower /= -huge(lower)) error stop 4
end program
