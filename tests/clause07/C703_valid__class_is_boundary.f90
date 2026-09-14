! rule: C703
! covers: class-is-boundary
! evidence: positive-control
program c703_class_is
    implicit none
    type, abstract :: root
        integer :: code
    end type
    type, extends(root) :: leaf
    end type
    class(root), allocatable :: object
    allocate(leaf :: object)
    if (.not. allocated(object)) error stop 'allocation'
    object%code = 17
    select type (object)
    class is (root)
        if (object%code /= 17) error stop 'value'
    class default
        error stop 'guard'
    end select
end program
