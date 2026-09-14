! rule: S6.2.5-002
! covers: duplicate-spelling
! evidence: positive-control
program label_duplicate
    implicit none
    integer :: value
    value = 7
10  continue
20  continue
    if (value /= 7) error stop 1
end program
