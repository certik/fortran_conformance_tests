! rule: S7.5.3.1-003
! covers: length-primary-in-component-length
! evidence: effect
! standard: f2023
program lengths
    implicit none
    type :: packet(count)
        integer, len :: count
        character(count) :: text
    end type
    type(packet(2)) :: a
    type(packet(3)) :: b
    if (a%count /= 2 .or. b%count /= 3) error stop 1
    if (len(a%text) /= 2 .or. len(b%text) /= 3) error stop 2
    a%text = 'ab'
    b%text = 'xyz'
    if (a%text /= 'ab' .or. b%text /= 'xyz') error stop 3
end program
