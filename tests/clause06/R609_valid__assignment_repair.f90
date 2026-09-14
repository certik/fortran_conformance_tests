! rule: R609
! covers: operator-generic-operand
! evidence: positive-control
program operator_membership
    implicit none
    type :: box
        integer :: value
    end type box
    interface operator (+)
        procedure :: sum_boxes
    end interface
    integer :: total

    total = sum_boxes(box(6), box(3))
    if (total /= 9) error stop 1
contains
    integer function sum_boxes(left, right) result(value)
        type(box), intent(in) :: left, right
        value = left%value + right%value
    end function sum_boxes
end program operator_membership
