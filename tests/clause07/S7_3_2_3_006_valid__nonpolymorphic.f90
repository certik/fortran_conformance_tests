! rule: S7.3.2.3-006
! covers: nonpolymorphic-inactive
! evidence: effect
program dynamic_nonpolymorphic_inactive
    implicit none
    type :: root
        integer :: tag
    end type
    type(root), allocatable :: a
    type(root), pointer :: p => null()
    type(root) :: mold
    mold%tag = 0
    if (allocated(a)) error stop 'allocatable-state'
    if (associated(p)) error stop 'pointer-state'
    if (.not. same_type_as(a, mold)) error stop 'allocatable-type'
    if (.not. same_type_as(p, mold)) error stop 'pointer-type'
end program
