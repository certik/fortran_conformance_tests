! rule: S7.4.3.1-007
! covers: long-leading-zero-boundary
! evidence: effect
! profile: integer-literal-default-binary31
! standard: f2023
program p
    implicit none
    integer :: positive, negative
    data positive /+0000000000000000000000000000000000000000000000002147483647/
    data negative /-0000000000000000000000000000000000000000000000002147483647/
    if (positive /= huge(positive)) error stop 1
    if (negative /= -huge(negative)) error stop 2
end program
