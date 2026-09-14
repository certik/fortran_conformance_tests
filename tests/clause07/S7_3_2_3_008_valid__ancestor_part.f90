! rule: S7.3.2.3-008
! covers: ancestor-part-pointer
! evidence: effect
program dynamic_ancestor_part
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: child
        integer :: extra
    end type
    class(root), allocatable, target :: actual
    type(root), pointer :: part => null()
    type(root) :: mold
    integer :: status = -1
    mold%base = 0
    allocate(child :: actual, stat=status)
    if (status /= 0) error stop 'target-allocation'
    if (.not. allocated(actual)) error stop 'target-unallocated'
    select type (actual)
    type is (child)
        actual%base = 11
        actual%extra = 79
    class default
        error stop 'target-type'
    end select
    part => actual
    if (.not. associated(part)) error stop 'ancestor-association'
    if (.not. same_type_as(part, mold)) error stop 'ancestor-dynamic-type'
    if (part%base /= 11) error stop 'ancestor-payload'
    part%base = 29
    select type (actual)
    type is (child)
        if (actual%base /= 29) error stop 'ancestor-alias'
        if (actual%extra /= 79) error stop 'extension-sentinel'
    class default
        error stop 'target-type-after-alias'
    end select
    nullify(part)
    deallocate(actual)
end program
