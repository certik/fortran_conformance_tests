! rule: R608
! covers: add-op
! evidence: positive-control
program intrinsic_add
    implicit none
    integer :: left, right, result

    left = 9
    right = 4
    result = left + right
    if (result /= 13) error stop 1
    result = left - right
    if (result /= 5) error stop 2
    result = +right
    if (result /= 4) error stop 3
    result = -right
    if (result /= -4) error stop 4
end program intrinsic_add
