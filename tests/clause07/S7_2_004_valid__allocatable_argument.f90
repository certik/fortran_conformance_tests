! rule: S7.2-004
! covers: allocatable-argument-character
! evidence: effect
program type_parameters_allocatable_argument
    implicit none
    character(len=:), allocatable :: text
    integer :: status

    allocate(character(len=3) :: text, stat=status)
    if (status /= 0) error stop 1
    if (.not. allocated(text)) error stop 2
    if (len(text) /= 3) error stop 3
    text(:) = 'ABC'
    call check_argument(text)
contains
    subroutine check_argument(argument)
        character(len=:), allocatable, intent(in) :: argument
        if (.not. allocated(argument)) error stop 4
        if (len(argument) /= 3) error stop 5
        if (argument /= 'ABC') error stop 6
    end subroutine check_argument
end program type_parameters_allocatable_argument
