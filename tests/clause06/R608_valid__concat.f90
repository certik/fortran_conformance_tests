! rule: R608
! covers: concat-op
! evidence: positive-control
program intrinsic_concat
    implicit none
    character(len=2) :: left, right
    character(len=4) :: result

    left = 'ab'
    right = 'CD'
    result = left // right
    if (result /= 'abCD') error stop 1
end program intrinsic_concat
