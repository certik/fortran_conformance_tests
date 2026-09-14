! rule: R610
! covers: not-op
! evidence: positive-control
module r610_not_m
    implicit none
    type :: flag
        logical :: set
    end type flag
    interface operator (.not.)
        module procedure invert_flag
    end interface
contains
    logical function invert_flag(operand) result(value)
        type(flag), intent(in) :: operand
        value = .not. operand%set
    end function invert_flag
end module r610_not_m

program extended_not
    use r610_not_m
    implicit none
    logical, parameter :: inputs(2) = [.false., .true.]
    integer, parameter :: expected(2) = [1, 0]
    type(flag) :: operand
    integer :: i
    logical :: result

    do i = 1, 2
        operand%set = inputs(i)
        result = .not. operand
        if (merge(1, 0, result) /= expected(i)) error stop 1
    end do
end program extended_not
