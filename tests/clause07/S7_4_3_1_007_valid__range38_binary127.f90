! rule: S7.4.3.1-007
! covers: long-leading-zero-boundary
! evidence: effect
! profile: integer-literal-range38-binary127
! standard: f2023
program p
    implicit none
    integer, parameter :: k = selected_int_kind(38)
    integer(k) :: positive, negative
    data positive /+000000000000000000000000000000000000000000000000170141183460469231731687303715884105727_k/
    data negative /-000000000000000000000000000000000000000000000000170141183460469231731687303715884105727_k/
    if (positive /= huge(positive)) error stop 1
    if (negative /= -huge(negative)) error stop 2
end program
