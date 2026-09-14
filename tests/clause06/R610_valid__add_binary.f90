! rule: R610
! covers: add-op
! evidence: positive-control
module r610_add_binary_m
    implicit none
    type :: box
        integer :: value
    end type box
    interface operator (+)
        module procedure add_boxes
    end interface
    interface operator (-)
        module procedure subtract_boxes
    end interface
contains
    integer function add_boxes(left, right) result(value)
        type(box), intent(in) :: left, right
        value = left%value + right%value
    end function add_boxes

    integer function subtract_boxes(left, right) result(value)
        type(box), intent(in) :: left, right
        value = left%value - right%value
    end function subtract_boxes
end module r610_add_binary_m

program extended_add_binary
    use r610_add_binary_m
    implicit none
    type(box) :: left, right
    integer :: result

    left%value = 13
    right%value = 5
    result = left + right
    if (result /= 18) error stop 1
    result = left - right
    if (result /= 8) error stop 2
end program extended_add_binary
