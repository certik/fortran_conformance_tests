! rule: R710
! covers: unsigned-digits plus-digits minus-digits
! evidence: positive-control
program p
    implicit none
    double precision :: a = 1.0d0, b = 1.0d+1, c = 1.0d-1
    if (a /= 1.0d0) error stop 1
    if (b /= 10.0d0) error stop 2
    if (c <= 0.0d0) error stop 3
    if (c >= 1.0d0) error stop 4
end program
