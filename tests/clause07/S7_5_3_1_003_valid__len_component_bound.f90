! rule: S7.5.3.1-003
! covers: length-primary-in-component-bound
! evidence: effect
! standard: f2023
program bounds
    implicit none
    type :: packet(extent)
        integer, len :: extent
        integer :: values(extent+1)
    end type
    type(packet(2)) :: a
    type(packet(4)) :: b
    if (a%extent /= 2 .or. b%extent /= 4) error stop 1
    if (size(a%values) /= 3 .or. size(b%values) /= 5) error stop 2
    if (lbound(a%values,1) /= 1 .or. lbound(b%values,1) /= 1) error stop 3
    a%values = 3
    b%values = 7
    if (any(a%values /= 3) .or. any(b%values /= 7)) error stop 4
end program
