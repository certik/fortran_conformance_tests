! rule: C702
! covers: character-allocatable
! evidence: positive-control
program type_parameters_allocatable
    implicit none
    character(len=:), allocatable :: text
    integer :: status

    allocate(character(len=2) :: text, stat=status)
    if (status /= 0) error stop 1
    if (.not. allocated(text)) error stop 2
    if (len(text) /= 2) error stop 3
    text(:) = 'AB'
    if (text /= 'AB') error stop 4
end program type_parameters_allocatable
