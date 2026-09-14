! rule: R610
! covers: power-op
! evidence: positive-control
module r610_power_m
    implicit none
    type :: box
        integer :: value
    end type box
    interface operator (**)
        module procedure pack_boxes
    end interface
contains
    integer function pack_boxes(left, right) result(value)
        type(box), intent(in) :: left, right
        ! The function, not intrinsic exponentiation, supplies this interpretation.
        value = 10 * left%value + right%value
    end function pack_boxes
end module r610_power_m

program extended_power
    use r610_power_m
    implicit none
    type(box) :: left, right
    integer :: result

    left%value = 3
    right%value = 4
    result = left ** right
    if (result /= 34) error stop 1
end program extended_power
