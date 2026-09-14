! rule: S7.4.3.1-007
! covers: long-leading-zero-boundary
! evidence: effect
! profile: integer-literal-range2-binary7
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(2)
    integer(k) :: positive, negative
    data positive /+000000000000000000000000000000000000000000000000127_k/
    data negative /-000000000000000000000000000000000000000000000000127_k/
    if (positive /= huge(positive)) error stop 1
    if (negative /= -huge(negative)) error stop 2
end program
