! rule: S7.5.3.1-002
! covers: expression-default-value
! evidence: effect
! standard: f2023
program defaults
    implicit none
    type :: packet(tag)
        integer, kind :: tag = 2+3
        integer :: payload
    end type
    type(packet) :: defaulted
    type(packet(7)) :: explicit_value
    defaulted%payload = 0
    explicit_value%payload = 0
    if (defaulted%tag /= 5) error stop 1
    if (explicit_value%tag /= 7) error stop 2
end program
