! rule: S6.2.5-001
! covers: nonblank-executable nonblank-nonexecutable
! evidence: positive-control
program label_nonblank
    implicit none
10  integer :: value
20  value = 7
    if (value /= 7) error stop 1
end program
