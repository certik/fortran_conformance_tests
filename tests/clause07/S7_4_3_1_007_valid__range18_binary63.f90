! rule: S7.4.3.1-007
! covers: long-leading-zero-boundary
! evidence: effect
! profile: integer-literal-range18-binary63
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(18)
    integer(k) :: positive, negative
    data positive /+0000000000000000000000000000000000000000000000009223372036854775807_k/
    data negative /-0000000000000000000000000000000000000000000000009223372036854775807_k/
    if (positive /= huge(positive)) error stop 1
    if (negative /= -huge(negative)) error stop 2
end program
