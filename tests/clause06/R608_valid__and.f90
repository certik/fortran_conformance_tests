! rule: R608
! covers: and-op
! evidence: positive-control
program intrinsic_and
    implicit none
    logical, parameter :: left(4) = [.false., .false., .true., .true.]
    logical, parameter :: right(4) = [.false., .true., .false., .true.]
    integer, parameter :: expected(4) = [0, 0, 0, 1]
    integer :: i
    logical :: result

    do i = 1, 4
        result = left(i) .and. right(i)
        if (merge(1, 0, result) /= expected(i)) error stop 1
    end do
end program intrinsic_and
