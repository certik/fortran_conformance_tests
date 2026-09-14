! rule: R707
! covers: unsigned plus minus kind-suffix
! evidence: positive-control
program p
    implicit none
    integer, parameter :: k = kind(0)
    integer :: a, b, c, d, e, f
    data a, b, c, d, e, f /13, +17, -19, 23_k, +29_k, -31_k/
    if (a /= 10 + 3) error stop 1
    if (b /= 10 + 7) error stop 2
    if (c /= 1 - 20) error stop 3
    if (d /= 20 + 3) error stop 4
    if (e /= 30 - 1) error stop 5
    if (f /= 0 - 30 - 1) error stop 6
end program
