! rule: R601
! covers: underscore-alternative
! evidence: positive-control
program alphaunderscore
    implicit none
    integer :: n, n_

    n = 3
    n_ = 8
    if (n /= 3) error stop 1
    if (n_ /= 8) error stop 2
end program alphaunderscore
