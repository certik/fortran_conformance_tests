! rule: R701
! covers: deferred-token
! evidence: positive-control
program type_parameters_deferred_token
    implicit none
    character(len=:), allocatable :: text
    integer :: status

    allocate(character(len=3) :: text, stat=status)
    if (status /= 0) error stop 1
    if (.not. allocated(text)) error stop 2
    if (len(text) /= 3) error stop 3
    text(:) = 'ABC'
    if (text /= 'ABC') error stop 4
end program type_parameters_deferred_token
