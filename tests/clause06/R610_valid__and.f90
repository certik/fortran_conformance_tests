! rule: R610
! covers: and-op
! evidence: positive-control
module r610_and_m
    implicit none
    type :: flag
        logical :: set
    end type flag
    interface operator (.and.)
        module procedure and_flags
    end interface
contains
    logical function and_flags(left, right) result(value)
        type(flag), intent(in) :: left, right
        value = left%set .and. right%set
    end function and_flags
end module r610_and_m

program extended_and
    use r610_and_m
    implicit none
    logical, parameter :: left_values(4) = [.false., .false., .true., .true.]
    logical, parameter :: right_values(4) = [.false., .true., .false., .true.]
    integer, parameter :: expected(4) = [0, 0, 0, 1]
    type(flag) :: left, right
    integer :: i
    logical :: result

    do i = 1, 4
        left%set = left_values(i)
        right%set = right_values(i)
        result = left .and. right
        if (merge(1, 0, result) /= expected(i)) error stop 1
    end do
end program extended_and
