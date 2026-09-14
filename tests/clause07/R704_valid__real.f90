! rule: R704
! covers: real-default real-selector
! evidence: positive-control
program p
    implicit none
    real :: a = 0.0
    real(kind=kind(0.0d0)) :: b = 0.0d0
    if (a /= 0.0) error stop 1
    if (b /= 0.0d0) error stop 2
end program
