! rule: R703
! covers: classof
! evidence: positive-control
! standard: f2023
program r703_classof
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload) :: seed = payload(3)
    classof(seed), allocatable :: value
    allocate(payload :: value)
    if (.not. allocated(value)) error stop 'allocation'
    value%code = 7
    if (value%code /= 7) error stop 'value'
end program
