! rule: C705
! covers: abstract-extensible
! evidence: positive-control
program c705_abstract
    implicit none
    type, abstract :: root
        integer :: code
    end type
    type, extends(root) :: leaf
    end type
    class(root), allocatable :: value
    allocate(leaf :: value)
    if (.not. allocated(value)) error stop 'allocation'
    value%code = 7
    if (value%code /= 7) error stop 'value'
end program
