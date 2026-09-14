! rule: R704
! covers: integer-alternative
! evidence: positive-control
program p
    implicit none
    integer :: a = 17
    integer(kind=kind(0)) :: b = -23
    if (a /= 17) error stop 1
    if (b /= -23) error stop 2
end program
