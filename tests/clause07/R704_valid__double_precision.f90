! rule: R704
! covers: double-precision
! evidence: positive-control
program p
    implicit none
    double precision :: a = 0.0d0
    if (a /= 0.0d0) error stop 1
end program
