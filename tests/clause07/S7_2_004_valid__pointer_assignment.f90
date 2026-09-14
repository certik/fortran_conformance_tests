! rule: S7.2-004
! covers: pointer-assignment-character
! evidence: effect
program type_parameters_deferred_pointer
    implicit none
    character(len=2), target :: first = 'AB'
    character(len=5), target :: second = 'ABCDE'
    character(len=:), pointer :: text => null()

    text => first
    if (.not. associated(text)) error stop 1
    if (len(text) /= 2) error stop 2
    if (text /= 'AB') error stop 3
    text => second
    if (.not. associated(text)) error stop 4
    if (len(text) /= 5) error stop 5
    if (text /= 'ABCDE') error stop 6
end program type_parameters_deferred_pointer
