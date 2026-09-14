! rule: R703
! covers: type-derived
! evidence: positive-control
program r703_type_derived
    implicit none
    type :: payload
        integer :: code
    end type
    type(payload) :: value
    value%code = 7
    if (value%code /= 7) error stop 'value'
end program
