! rule: C702
! covers: character-pointer
! evidence: positive-control
program type_parameters_pointer
    implicit none
    character(len=4), target :: target = 'ABCD'
    character(len=:), pointer :: text => null()

    text => target
    if (.not. associated(text)) error stop 1
    if (len(text) /= 4) error stop 2
    if (text /= 'ABCD') error stop 3
end program type_parameters_pointer
