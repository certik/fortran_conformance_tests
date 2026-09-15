! rule: S7.4.4.2-006
! covers: pointer-assumed-dummy
! evidence: effect
! standard: f2023
program character_type_case
    implicit none
    character(3), target :: target
    character(3), pointer :: text
    target = 'xyz'
    text => target
    call check(text)
contains
    subroutine check(value)
        character(*), pointer, intent(in) :: value
        if (.not. associated(value)) error stop 1
        if (len(value) /= 3) error stop 2
        if (value /= 'xyz') error stop 3
    end subroutine
end program
