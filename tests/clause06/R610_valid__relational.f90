! rule: R610
! covers: rel-op
! evidence: positive-control
module r610_relational_m
    implicit none
    type :: box
        integer :: value
    end type box
    interface operator (<)
        module procedure less_box
    end interface
contains
    logical function less_box(left, right) result(value)
        type(box), intent(in) :: left, right
        value = left%value < right%value
    end function less_box
end module r610_relational_m

program extended_relational
    use r610_relational_m
    implicit none
    integer, parameter :: left_values(3) = [2, 5, 2]
    integer, parameter :: right_values(3) = [5, 2, 2]
    integer, parameter :: expected(3) = [1, 0, 0]
    type(box) :: left, right
    integer :: i
    logical :: result

    do i = 1, 3
        left%value = left_values(i)
        right%value = right_values(i)
        result = left < right
        if (merge(1, 0, result) /= expected(i)) error stop 1
    end do
end program extended_relational
