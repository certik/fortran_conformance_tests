! rule: S7.3.2.3-004
! covers: concrete-extension-target sibling-reassociation
! evidence: effect
program dynamic_sibling_targets
    implicit none
    type :: root
        integer :: base
    end type
    type, extends(root) :: left
        integer :: left_tag
    end type
    type, extends(root) :: right
        integer :: right_tag
    end type
    type(left), target :: first
    type(right), target :: second
    class(root), pointer :: p => null()
    first%base = 11
    first%left_tag = 13
    second%base = 17
    second%right_tag = 19
    p => first
    if (.not. associated(p)) error stop 'first-association'
    select type (p)
    type is (left)
        if (p%base /= 11) error stop 'first-base'
        if (p%left_tag /= 13) error stop 'first-extension'
    class default
        error stop 'first-dynamic-type'
    end select
    p => second
    if (.not. associated(p)) error stop 'second-association'
    select type (p)
    type is (right)
        if (p%base /= 17) error stop 'second-base'
        if (p%right_tag /= 19) error stop 'second-extension'
    class default
        error stop 'second-dynamic-type'
    end select
    nullify(p)
end program
