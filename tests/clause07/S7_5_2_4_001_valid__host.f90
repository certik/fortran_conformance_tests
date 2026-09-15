! rule: S7.5.2.4-001
! covers: host-associated-definition
! evidence: effect
! standard: f2023
program p
    implicit none
    type :: record
        integer :: payload
    end type
    type(record) :: value
    value%payload = 11
    call change(value)
    if (value%payload /= 13) error stop 1
contains
    subroutine change(item)
        type(record), intent(inout) :: item
        if (item%payload /= 11) error stop 2
        item%payload = 13
    end subroutine
end program
