! rule: R706
! covers: positional-expression keyword-expression
! evidence: positive-control
program p
    implicit none
    integer, parameter :: selector = kind(0)
    integer(selector + 0) :: a = 13
    integer(kind=kind(0) + 0) :: b = -19
    if (kind(a) /= kind(0)) error stop 1
    if (kind(b) /= kind(0)) error stop 2
    if (a /= 13) error stop 3
    if (b /= -19) error stop 4
end program
