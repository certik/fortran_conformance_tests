! rule: S7.2-004
! covers: intrinsic-assignment-character
! evidence: effect
program type_parameters_deferred_assignment
    implicit none
    character(len=:), allocatable :: text

    text = 'AB'
    if (.not. allocated(text)) error stop 1
    if (len(text) /= 2) error stop 2
    if (text /= 'AB') error stop 3
    text = 'ABCDE'
    if (.not. allocated(text)) error stop 4
    if (len(text) /= 5) error stop 5
    if (text /= 'ABCDE') error stop 6
end program type_parameters_deferred_assignment
