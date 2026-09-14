! rule: S7.4.3.1-005
! covers: small-default-values
! evidence: effect
program p
    implicit none
    integer :: a, b, c, d
    data a, b, c, d /0, +19, -23, 99999/
    if (a /= 1 - 1) error stop 1
    if (b /= 20 - 1) error stop 2
    if (c /= 0 - 20 - 3) error stop 3
    if (d /= 9 * 10000 + 9999) error stop 4
end program
