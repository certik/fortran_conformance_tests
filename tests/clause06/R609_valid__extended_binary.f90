! rule: R609
! covers: extended-intrinsic-op
! evidence: positive-control
module r609_extended_binary_m
    implicit none
    type :: box
        integer :: value
    end type box
    interface operator (+)
        module procedure add_boxes
    end interface
contains
    integer function add_boxes(left, right) result(value)
        type(box), intent(in) :: left, right
        value = left%value + right%value
    end function add_boxes
end module r609_extended_binary_m

program defined_intrinsic_binary
    use r609_extended_binary_m
    implicit none
    type(box) :: left, right
    integer :: result

    left%value = 6
    right%value = 3
    result = left + right
    if (result /= 9) error stop 1
end program defined_intrinsic_binary
