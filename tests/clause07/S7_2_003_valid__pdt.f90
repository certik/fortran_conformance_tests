! rule: S7.2-003
! covers: pdt-kind-and-length-selection
! evidence: effect
module type_parameters_pdt_generic
    implicit none
    type :: token(selector, width)
        integer, kind :: selector
        integer, len :: width
        integer :: payload
    end type token
    interface identify
        module procedure first_tag, second_tag
    end interface
contains
    integer function first_tag(value) result(tag)
        type(token(1, *)), intent(in) :: value
        if (value%selector /= 1) error stop 1
        if (value%payload /= 7) error stop 2
        tag = 100 + value%width
    end function first_tag

    integer function second_tag(value) result(tag)
        type(token(2, *)), intent(in) :: value
        if (value%selector /= 2) error stop 3
        if (value%payload /= 11) error stop 4
        tag = 200 + value%width
    end function second_tag
end module type_parameters_pdt_generic

program type_parameters_pdt_dispatch
    use type_parameters_pdt_generic, only: token, identify
    implicit none
    type(token(1, 2)) :: short
    type(token(1, 4)) :: long
    type(token(2, 2)) :: other

    short%payload = 7
    long%payload = 7
    other%payload = 11
    if (identify(short) /= 102) error stop 5
    if (identify(long) /= 104) error stop 6
    if (identify(other) /= 202) error stop 7
end program type_parameters_pdt_dispatch
