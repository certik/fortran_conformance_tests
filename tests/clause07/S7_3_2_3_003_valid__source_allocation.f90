! rule: S7.3.2.3-003
! covers: source-dynamic-type
! evidence: effect
program dynamic_source_allocation
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: child
        integer :: extra
    end type
    class(root), allocatable :: source, value
    integer :: status = -1
    allocate(child :: source, stat=status)
    if (status /= 0) error stop 'source-allocation'
    if (.not. allocated(source)) error stop 'source-unallocated'
    select type (source)
    type is (child)
        source%base = 23
        source%extra = 29
    class default
        error stop 'source-dynamic-type'
    end select
    status = -1
    allocate(value, source=source, stat=status)
    if (status /= 0) error stop 'destination-allocation'
    if (.not. allocated(value)) error stop 'destination-unallocated'
    select type (value)
    type is (child)
        if (value%base /= 23) error stop 'copied-base'
        if (value%extra /= 29) error stop 'copied-extension'
    class default
        error stop 'copied-dynamic-type'
    end select
    deallocate(value, source)
end program
