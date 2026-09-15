! rule: S7.5.3.1-004
! covers: prior-kind-in-integer-selector
! evidence: effect
! standard: f2023
program selectors
    implicit none
    integer, parameter :: ik = selected_int_kind(18)
    type :: packet(carrier,count)
        integer, kind :: carrier = kind(0)
        integer(carrier), len :: count = 3
        integer :: value
    end type
    type(packet) :: a
    type(packet(ik)) :: b
    a%value = 0
    b%value = 0
    if (a%carrier /= kind(0) .or. b%carrier /= ik) error stop 1
    if (kind(a%count) /= kind(0) .or. kind(b%count) /= ik) error stop 2
    call default_value(a%count)
    call selected_value(b%count)
contains
    subroutine default_value(value)
        integer, intent(in) :: value
        if (value /= 3) error stop 3
    end subroutine
    subroutine selected_value(value)
        integer(ik), intent(in) :: value
        if (value /= 3_ik) error stop 4
    end subroutine
end program
