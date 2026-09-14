! rule: C706
! covers: concrete-type
! evidence: positive-control
program c706_type
    implicit none
    type :: root
        integer :: code
    end type
    type(root) :: value
    value%code = 7
    if (value%code /= 7) error stop 'value'
end program
