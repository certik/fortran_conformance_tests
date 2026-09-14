! rule: S7.4.3.1-007
! covers: long-leading-zero-boundary
! evidence: effect
! profile: integer-literal-range4-binary15
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(4)
    integer(k) :: positive, negative
    data positive /+00000000000000000000000000000000000000000000000032767_k/
    data negative /-00000000000000000000000000000000000000000000000032767_k/
    if (positive /= huge(positive)) error stop 1
    if (negative /= -huge(negative)) error stop 2
end program
