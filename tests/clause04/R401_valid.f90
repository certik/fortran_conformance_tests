! rule: R401
! covers: singleton-control comma-repetition-control
! evidence: positive-control
program assumed_list
    implicit none
    integer :: single
    integer :: first, second
    integer :: left, middle, right
    single = 1
    first = 2
    second = 3
    left = 4
    middle = 5
    right = 6
    if (single /= 1) stop 1
    if (first /= 2) stop 2
    if (second /= 3) stop 3
    if (left /= 4) stop 4
    if (middle /= 5) stop 5
    if (right /= 6) stop 6
end program assumed_list
