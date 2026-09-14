! rule: C703
! covers: concrete-type-spec
! evidence: positive-control
program c703_allocate
    implicit none
    type, abstract :: root
        integer :: code
    end type
    type, extends(root) :: leaf
    end type
    class(root), allocatable :: object
    allocate(leaf :: object)
    if (.not. allocated(object)) error stop 'allocation'
    object%code = 7
    if (object%code /= 7) error stop 'value'
end program
