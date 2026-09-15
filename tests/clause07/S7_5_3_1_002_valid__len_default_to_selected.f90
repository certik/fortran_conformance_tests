! rule: S7.5.3.1-002
! covers: default-to-selected-integer-conversion
! evidence: effect
! standard: f2023
program parameter_probe
    implicit none
integer, parameter :: ik = selected_int_kind(18)
    type :: packet(tag)
        integer(ik), len :: tag = 3
        integer :: payload
    end type
    type(packet) :: item
    item%payload = 7
    if (item%tag /= 3) error stop 1
    if (kind(item%tag) /= ik) error stop 2
    call check(item%tag)
contains
    subroutine check(value)
        integer(ik), intent(in) :: value
        if (value /= 3) error stop 3
    end subroutine
end program
