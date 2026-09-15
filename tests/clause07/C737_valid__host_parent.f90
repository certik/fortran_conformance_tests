! rule: C737
! covers: renamed-or-host-parent
! evidence: positive-control
! standard: f2023
program p
    implicit none
    type :: parent
        integer :: payload
    end type
    call check()
contains
    subroutine check()
        type, extends(parent) :: child
        end type
        type(child) :: value
        value%payload = 17
        if (value%payload /= 17) error stop 1
    end subroutine
end program
