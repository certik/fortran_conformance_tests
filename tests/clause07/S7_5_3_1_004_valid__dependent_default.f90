! rule: S7.5.3.1-004
! covers: prior-kind-in-parameter-default
! evidence: effect
! standard: f2023
program defaults
    implicit none
    type :: packet(tag,extent)
        integer, kind :: tag = 2
        integer, len :: extent = tag+1
        integer :: value
    end type
    type(packet) :: a
    type(packet(tag=5)) :: b
    a%value = 0
    b%value = 0
    if (a%tag /= 2 .or. a%extent /= 3) error stop 1
    if (b%tag /= 5 .or. b%extent /= 6) error stop 2
end program
