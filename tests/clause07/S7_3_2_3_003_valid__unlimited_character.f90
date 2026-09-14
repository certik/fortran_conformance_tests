! rule: S7.3.2.3-003
! covers: unlimited-character-lengths
! evidence: effect
program dynamic_unlimited_character
    implicit none
    class(*), allocatable :: value
    integer :: status = -1
    allocate(character(len=3) :: value, stat=status)
    if (status /= 0) error stop 'short-allocation'
    if (.not. allocated(value)) error stop 'short-unallocated'
    select type (value)
    type is (character(len=*))
        if (len(value) /= 3) error stop 'short-length'
        value = 'oak'
        if (value /= 'oak') error stop 'short-value'
    class default
        error stop 'short-type'
    end select
    deallocate(value)
    status = -1
    allocate(character(len=5) :: value, stat=status)
    if (status /= 0) error stop 'long-allocation'
    if (.not. allocated(value)) error stop 'long-unallocated'
    select type (value)
    type is (character(len=*))
        if (len(value) /= 5) error stop 'long-length'
        value = 'birch'
        if (value /= 'birch') error stop 'long-value'
    class default
        error stop 'long-type'
    end select
    deallocate(value)
end program
