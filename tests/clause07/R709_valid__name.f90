! rule: R709
! covers: constant-name
! evidence: positive-control
program p
    implicit none
    integer, parameter :: selector = kind(0)
    integer :: value
    data value /43_selector/
    if (value /= 40 + 3) error stop 1
end program
