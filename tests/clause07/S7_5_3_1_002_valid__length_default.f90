! rule: S7.5.3.1-002
! covers: length-default-value
! evidence: effect
! standard: f2023
program parameter_probe
    implicit none

    type :: packet(tag)
        integer, len :: tag = 3
        integer :: payload
    end type
    type(packet) :: item
    item%payload = 7
    if (item%tag /= 3) error stop 1
    if (kind(item%tag) /= kind(0)) error stop 2
    call check(item%tag)
contains
    subroutine check(value)
        integer(kind(0)), intent(in) :: value
        if (value /= 3) error stop 3
    end subroutine
end program
