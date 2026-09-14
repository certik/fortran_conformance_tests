! rule: R608
! covers: not-op
! evidence: positive-control
program intrinsic_not
    implicit none
    logical, parameter :: operand(2) = [.false., .true.]
    integer, parameter :: expected(2) = [1, 0]
    integer :: i
    logical :: result

    do i = 1, 2
        result = .not. operand(i)
        if (merge(1, 0, result) /= expected(i)) error stop 1
    end do
end program intrinsic_not
