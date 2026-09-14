! rule: R602
! covers: underscore-terminal
! evidence: positive-control
program underscoreterminal
    implicit none
    integer :: left_right, leftright

    left_right = 17
    leftright = 29
    if (left_right /= 17) error stop 1
    if (leftright /= 29) error stop 2
end program underscoreterminal
