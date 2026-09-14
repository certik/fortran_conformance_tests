! rule: R712
! covers: plus minus
! evidence: positive-control
program p
    implicit none
    integer :: positive, negative
    data positive, negative /+37, -41/
    if (positive /= 30 + 7) error stop 1
    if (negative /= 0 - 40 - 1) error stop 2
end program
