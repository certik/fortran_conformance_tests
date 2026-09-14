! rule: S7.3.2.3-003
! covers: declared-type-allocation extension-allocation
! evidence: effect
program dynamic_named_allocation
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: branch
        integer :: middle
    end type
    type, extends(branch) :: leaf
        integer :: tip
    end type
    class(root), allocatable :: value
    integer :: status = -1
    allocate(root :: value, stat=status)
    if (status /= 0) error stop 'root-allocation'
    if (.not. allocated(value)) error stop 'root-unallocated'
    select type (value)
    type is (root)
        value%base = 11
        if (value%base /= 11) error stop 'root-payload'
    class default
        error stop 'root-dynamic-type'
    end select
    deallocate(value)
    status = -1
    allocate(leaf :: value, stat=status)
    if (status /= 0) error stop 'leaf-allocation'
    if (.not. allocated(value)) error stop 'leaf-unallocated'
    select type (value)
    type is (leaf)
        value%base = 13
        value%middle = 17
        value%tip = 19
        if (value%base /= 13) error stop 'inherited-root'
        if (value%middle /= 17) error stop 'inherited-branch'
        if (value%tip /= 19) error stop 'leaf-payload'
    class default
        error stop 'leaf-dynamic-type'
    end select
    deallocate(value)
end program
