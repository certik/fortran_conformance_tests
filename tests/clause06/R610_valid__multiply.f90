! rule: R610
! covers: mult-op
! evidence: positive-control
module r610_multiply_m
    implicit none
    type :: box
        integer :: value
    end type box
    interface operator (*)
        module procedure multiply_boxes
    end interface
    interface operator (/)
        module procedure divide_boxes
    end interface
contains
    integer function multiply_boxes(left, right) result(value)
        type(box), intent(in) :: left, right
        value = left%value * right%value
    end function multiply_boxes

    integer function divide_boxes(left, right) result(value)
        type(box), intent(in) :: left, right
        value = left%value / right%value
    end function divide_boxes
end module r610_multiply_m

program extended_multiply
    use r610_multiply_m
    implicit none
    type(box) :: left, right
    integer :: result

    left%value = 18
    right%value = 3
    result = left * right
    if (result /= 54) error stop 1
    result = left / right
    if (result /= 6) error stop 2
end program extended_multiply
