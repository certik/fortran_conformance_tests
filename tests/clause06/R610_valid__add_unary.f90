! rule: R610
! covers: add-op
! evidence: positive-control
module r610_add_unary_m
    implicit none
    type :: box
        integer :: value
    end type box
    interface operator (+)
        module procedure positive_box
    end interface
    interface operator (-)
        module procedure negative_box
    end interface
contains
    integer function positive_box(operand) result(value)
        type(box), intent(in) :: operand
        value = operand%value
    end function positive_box

    integer function negative_box(operand) result(value)
        type(box), intent(in) :: operand
        value = -operand%value
    end function negative_box
end module r610_add_unary_m

program extended_add_unary
    use r610_add_unary_m
    implicit none
    type(box) :: operand
    integer :: result

    operand%value = 7
    result = +operand
    if (result /= 7) error stop 1
    result = -operand
    if (result /= -7) error stop 2
end program extended_add_unary
