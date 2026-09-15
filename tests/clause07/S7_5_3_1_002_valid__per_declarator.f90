! rule: S7.5.3.1-002
! covers: defaults-per-declarator
! evidence: effect
! standard: f2023
program defaults
    implicit none
    type :: packet(left,right)
        integer, kind :: left = 2, right = 5
        integer :: payload
    end type
    type(packet) :: item
    item%payload = 0
    if (item%left /= 2) error stop 1
    if (item%right /= 5) error stop 2
end program
