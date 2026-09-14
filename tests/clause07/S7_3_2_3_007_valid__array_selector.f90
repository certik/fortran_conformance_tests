! rule: S7.3.2.3-007
! covers: polymorphic-array-selector
! evidence: effect
program dynamic_array_selector
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: child
        integer :: extra
    end type
    class(root), allocatable :: actual(:)
    integer :: status = -1
    allocate(child :: actual(2), stat=status)
    if (status /= 0) error stop 'selector-allocation'
    if (.not. allocated(actual)) error stop 'selector-unallocated'
    if (size(actual) /= 2) error stop 'selector-size'
    select type (actual)
    type is (child)
        actual%base = [2, 3]
        actual%extra = [5, 7]
    class default
        error stop 'selector-type'
    end select
    associate (named => actual)
        if (rank(named) /= 1) error stop 'associate-rank'
        if (size(named) /= 2) error stop 'associate-size'
        select type (value => named)
        type is (child)
            if (any(value%base /= [2, 3])) error stop 'associate-base'
            if (any(value%extra /= [5, 7])) error stop 'associate-extension'
            value(2)%base = 13
        class default
            error stop 'associate-dynamic-type'
        end select
    end associate
    if (actual(2)%base /= 13) error stop 'associate-alias'
    deallocate(actual)
end program
