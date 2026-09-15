! rule: S7.5.3.1-002
! covers: selected-to-default-integer-conversion
! evidence: effect
! standard: f2023
program parameter_probe
    implicit none
integer, parameter :: ik = selected_int_kind(18)
    type :: packet(tag)
        integer, kind :: tag = -2_ik
        integer :: payload
    end type
    type(packet) :: item
    item%payload = 7
    if (item%tag /= -2) error stop 1
    if (kind(item%tag) /= kind(0)) error stop 2
    call check(item%tag)
contains
    subroutine check(value)
        integer(kind(0)), intent(in) :: value
        if (value /= -2) error stop 3
    end subroutine
end program
