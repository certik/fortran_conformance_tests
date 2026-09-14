! rule: R704
! covers: complex-default complex-selector
! evidence: positive-control
program p
    implicit none
    complex :: a = (0.0, 0.0)
    complex(kind=kind(0.0d0)) :: b = (0.0d0, 0.0d0)
    if (a /= (0.0, 0.0)) error stop 1
    if (b /= (0.0d0, 0.0d0)) error stop 2
end program
