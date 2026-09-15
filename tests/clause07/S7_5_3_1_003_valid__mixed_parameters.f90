! rule: S7.5.3.1-003
! covers: mixed-parameter-expression
! evidence: effect
! standard: f2023
program bounds
    implicit none
    type :: packet(tag,extent)
        integer, kind :: tag
        integer, len :: extent
        integer :: values(tag+extent)
    end type
    type(packet(2,3)) :: a
    type(packet(3,4)) :: b
    if (a%tag /= 2 .or. a%extent /= 3) error stop 1
    if (b%tag /= 3 .or. b%extent /= 4) error stop 2
    if (size(a%values) /= 5 .or. size(b%values) /= 7) error stop 3
    a%values = 1
    b%values = 2
    if (any(a%values /= 1) .or. any(b%values /= 2)) error stop 4
end program
