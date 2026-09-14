! rule: S7.3.2.3-007
! covers: pointer-selector
! evidence: effect
program dynamic_pointer_selector
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: child
        integer :: extra
    end type
    type(child), target :: actual
    class(root), pointer :: p => null()
    actual%base = 31
    actual%extra = 37
    p => actual
    if (.not. associated(p)) error stop 'selector-association'
    associate (named => p)
        select type (value => named)
        type is (child)
            if (value%base /= 31) error stop 'associate-base'
            if (value%extra /= 37) error stop 'associate-extension'
        class default
            error stop 'associate-dynamic-type'
        end select
    end associate
    nullify(p)
end program
