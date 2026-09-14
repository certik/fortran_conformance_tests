! rule: S7.3.2.3-006
! covers: initial-disassociated after-nullify
! evidence: effect
program dynamic_disassociated
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: child
        integer :: extra
    end type
    class(root), pointer :: value => null()
    type(root) :: root_mold
    type(child), target :: child_target
    root_mold%base = 0
    child_target%base = 17
    child_target%extra = 19
    if (associated(value)) error stop 'initial-association-state'
    if (.not. same_type_as(value, root_mold)) error stop 'initial-root-type'
    if (same_type_as(value, child_target)) error stop 'initial-child-type'
    value => child_target
    if (.not. associated(value)) error stop 'association'
    if (.not. same_type_as(value, child_target)) error stop 'active-child-type'
    nullify(value)
    if (associated(value)) error stop 'nullify-state'
    if (.not. same_type_as(value, root_mold)) error stop 'restored-root-type'
    if (same_type_as(value, child_target)) error stop 'stale-child-type'
end program
