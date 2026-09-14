! rule: S7.2-004
! covers: allocate-character
! evidence: effect
program type_parameters_deferred_allocate
    implicit none
    character(len=:), allocatable :: text(:)
    integer :: status

    allocate(character(len=3) :: text(2), stat=status)
    if (status /= 0) error stop 1
    if (.not. allocated(text)) error stop 2
    if (size(text) /= 2) error stop 3
    if (lbound(text, 1) /= 1) error stop 4
    if (len(text) /= 3) error stop 5
    text(:) = 'ABC'
    if (text(1) /= 'ABC') error stop 6
    if (text(2) /= 'ABC') error stop 7
end program type_parameters_deferred_allocate
