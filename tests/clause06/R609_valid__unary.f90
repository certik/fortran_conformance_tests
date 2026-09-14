! rule: R609
! covers: defined-unary-op
! evidence: positive-control
module r609_unary_m
    implicit none
    interface operator (.shift.)
        module procedure shift_integer
    end interface
contains
    integer function shift_integer(operand) result(value)
        integer, intent(in) :: operand
        value = operand + 5
    end function shift_integer
end module r609_unary_m

program defined_unary
    use r609_unary_m
    implicit none
    integer :: operand, result

    operand = 7
    result = .shift. operand
    if (result /= 12) error stop 1
end program defined_unary
