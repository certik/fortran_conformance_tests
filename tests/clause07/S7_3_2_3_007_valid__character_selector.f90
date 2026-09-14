! rule: S7.3.2.3-007
! covers: unlimited-character-selector
! evidence: effect
program dynamic_character_selector
    implicit none
    class(*), allocatable :: actual
    integer :: status = -1
    allocate(character(len=3) :: actual, stat=status)
    if (status /= 0) error stop 'selector-allocation'
    if (.not. allocated(actual)) error stop 'selector-unallocated'
    select type (actual)
    type is (character(len=*))
        if (len(actual) /= 3) error stop 'selector-length'
        actual = 'elm'
    class default
        error stop 'selector-type'
    end select
    associate (named => actual)
        select type (value => named)
        type is (character(len=*))
            if (len(value) /= 3) error stop 'associate-length'
            if (value /= 'elm') error stop 'associate-payload'
        class default
            error stop 'associate-dynamic-type'
        end select
    end associate
    deallocate(actual)
end program
