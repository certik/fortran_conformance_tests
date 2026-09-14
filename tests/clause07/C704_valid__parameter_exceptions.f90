! rule: C704
! covers: deferred-colon assumed-asterisk
! evidence: positive-control
program c704_exceptions
    implicit none
    call inspect('abc')
contains
    subroutine inspect(seed)
        character(*), intent(in) :: seed
        character(:), allocatable :: copy
        allocate(character(5) :: copy)
        if (.not. allocated(copy)) error stop 'allocation'
        copy(:) = 'hello'
        if (len(seed) /= 3 .or. len(copy) /= 5) error stop 'lengths'
        if (seed /= 'abc' .or. copy /= 'hello') error stop 'values'
    end subroutine
end program
