! rule: R708
! covers: digits-only kind-suffix
! evidence: positive-control
program p
    implicit none
    integer, parameter :: k = kind(0)
    integer :: a, b
    data a, b /37, 41_k/
    if (a /= 30 + 7) error stop 1
    if (b /= 40 + 1) error stop 2
end program
