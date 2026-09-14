! rule: R608
! covers: mult-op
! evidence: positive-control
program intrinsic_multiply
    implicit none
    integer :: left, right, result

    left = 21
    right = 3
    result = left * right
    if (result /= 63) error stop 1
    result = left / right
    if (result /= 7) error stop 2
end program intrinsic_multiply
