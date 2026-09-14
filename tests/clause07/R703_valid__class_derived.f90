! rule: R703
! covers: class-derived
! evidence: positive-control
program r703_class_derived
    implicit none
    type :: payload
        integer :: code
    end type
    class(payload), allocatable :: value
    allocate(payload :: value)
    if (.not. allocated(value)) error stop 'allocation'
    value%code = 7
    if (value%code /= 7) error stop 'value'
end program
