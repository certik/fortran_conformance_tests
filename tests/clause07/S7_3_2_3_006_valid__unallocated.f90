! rule: S7.3.2.3-006
! covers: initial-unallocated after-deallocation
! evidence: effect
program dynamic_unallocated
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: child
        integer :: extra
    end type
    class(root), allocatable :: value
    type(root) :: root_mold
    type(child) :: child_mold
    integer :: status = -1
    root_mold%base = 0
    child_mold%base = 0
    child_mold%extra = 0
    if (allocated(value)) error stop 'initial-allocation-state'
    if (.not. same_type_as(value, root_mold)) error stop 'initial-root-type'
    if (same_type_as(value, child_mold)) error stop 'initial-child-type'
    allocate(child :: value, stat=status)
    if (status /= 0) error stop 'allocation'
    if (.not. allocated(value)) error stop 'unallocated-after-allocate'
    select type (value)
    type is (child)
        value%base = 17
        value%extra = 19
    class default
        error stop 'allocated-type'
    end select
    if (.not. same_type_as(value, child_mold)) error stop 'active-child-type'
    deallocate(value)
    if (allocated(value)) error stop 'deallocation-state'
    if (.not. same_type_as(value, root_mold)) error stop 'restored-root-type'
    if (same_type_as(value, child_mold)) error stop 'stale-child-type'
end program
