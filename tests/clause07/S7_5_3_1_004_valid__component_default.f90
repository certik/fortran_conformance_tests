! rule: S7.5.3.1-004
! covers: prior-kind-in-component-initialization
! evidence: effect
! standard: f2023
program initialized
    implicit none
    type :: packet(tag)
        integer, kind :: tag
        integer :: value = tag+2
    end type
    type(packet(2)) :: a
    type(packet(5)) :: b
    if (a%value /= 4 .or. b%value /= 7) error stop 1
end program
