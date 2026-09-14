! rule: S7.3.2.3-004
! covers: polymorphic-target-dynamic
! evidence: effect
program dynamic_polymorphic_target
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: child
        integer :: extra
    end type
    class(root), allocatable, target :: storage
    class(root), pointer :: p => null()
    integer :: status = -1
    allocate(child :: storage, stat=status)
    if (status /= 0) error stop 'target-allocation'
    if (.not. allocated(storage)) error stop 'target-unallocated'
    select type (storage)
    type is (child)
        storage%base = 23
        storage%extra = 31
    class default
        error stop 'target-dynamic-type'
    end select
    p => storage
    if (.not. associated(p)) error stop 'pointer-association'
    select type (p)
    type is (child)
        if (p%base /= 23) error stop 'target-base'
        if (p%extra /= 31) error stop 'target-extension'
    class default
        error stop 'pointer-took-declared-type'
    end select
    nullify(p)
    deallocate(storage)
end program
