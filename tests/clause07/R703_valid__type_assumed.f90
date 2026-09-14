! rule: R703
! covers: type-assumed
! evidence: positive-control
program r703_type_assumed
    implicit none
    call inspect(7)
contains
    subroutine inspect(value)
        type(*), optional, intent(in) :: value
        if (.not. present(value)) error stop 'present'
    end subroutine
end program
