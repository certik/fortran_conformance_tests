! rule: R606
! covers: scalar-name
! evidence: positive-control
program scalar_named_constant
    implicit none
    integer, parameter :: repeats = 2
    integer :: values(2)
    data values /repeats * 7/

    if (values(1) /= 7) error stop 1
    if (values(2) /= 7) error stop 2
end program scalar_named_constant
