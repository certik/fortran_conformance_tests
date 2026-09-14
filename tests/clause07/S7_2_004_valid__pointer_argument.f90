! rule: S7.2-004
! covers: pointer-argument-character
! evidence: effect
program type_parameters_pointer_argument
    implicit none
    character(len=4), target :: target = 'ABCD'
    character(len=:), pointer :: text => null()

    text => target
    if (.not. associated(text)) error stop 1
    if (len(text) /= 4) error stop 2
    call check_argument(text)
contains
    subroutine check_argument(argument)
        character(len=:), pointer, intent(in) :: argument
        if (.not. associated(argument)) error stop 3
        if (len(argument) /= 4) error stop 4
        if (argument /= 'ABCD') error stop 5
    end subroutine check_argument
end program type_parameters_pointer_argument
