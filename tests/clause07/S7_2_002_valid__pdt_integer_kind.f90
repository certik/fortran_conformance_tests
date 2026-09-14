! rule: S7.2-002
! covers: pdt-integer-parameter-kinds
! evidence: effect
! standard: f2023
program type_parameters_integer_parameter_kind
    implicit none
    integer, parameter :: parameter_kind = selected_int_kind(18)
    type :: packet(selector, width)
        integer(kind=parameter_kind), kind :: selector
        integer(kind=parameter_kind), len :: width
        integer :: payload(width)
    end type packet
    type(packet(2_parameter_kind, 3_parameter_kind)) :: value

    if (kind(value%selector) /= parameter_kind) error stop 1
    if (kind(value%width) /= parameter_kind) error stop 2
    call check_parameter(value%selector, 2_parameter_kind)
    call check_parameter(value%width, 3_parameter_kind)
    if (size(value%payload) /= 3) error stop 3
    if (lbound(value%payload, 1) /= 1) error stop 4
    value%payload = [7, 11, 13]
    if (value%payload(1) /= 7) error stop 5
    if (value%payload(2) /= 11) error stop 6
    if (value%payload(3) /= 13) error stop 7
contains
    subroutine check_parameter(actual, expected)
        integer(kind=parameter_kind), intent(in) :: actual, expected
        if (actual /= expected) error stop 8
    end subroutine check_parameter
end program type_parameters_integer_parameter_kind
