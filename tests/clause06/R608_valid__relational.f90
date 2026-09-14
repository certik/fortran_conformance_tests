! rule: R608
! covers: rel-op
! evidence: positive-control
program intrinsic_relations
    implicit none
    integer, parameter :: left(3) = [2, 2, 5]
    integer, parameter :: right(3) = [5, 2, 2]
    integer, parameter :: equal(3) = [0, 1, 0]
    integer, parameter :: unequal(3) = [1, 0, 1]
    integer, parameter :: less(3) = [1, 0, 0]
    integer, parameter :: less_equal(3) = [1, 1, 0]
    integer, parameter :: greater(3) = [0, 0, 1]
    integer, parameter :: greater_equal(3) = [0, 1, 1]
    integer :: i
    logical :: result

    do i = 1, 3
        result = left(i) .eq. right(i)
        if (merge(1, 0, result) /= equal(i)) error stop 1
        result = left(i) .ne. right(i)
        if (merge(1, 0, result) /= unequal(i)) error stop 2
        result = left(i) .lt. right(i)
        if (merge(1, 0, result) /= less(i)) error stop 3
        result = left(i) .le. right(i)
        if (merge(1, 0, result) /= less_equal(i)) error stop 4
        result = left(i) .gt. right(i)
        if (merge(1, 0, result) /= greater(i)) error stop 5
        result = left(i) .ge. right(i)
        if (merge(1, 0, result) /= greater_equal(i)) error stop 6
        result = left(i) == right(i)
        if (merge(1, 0, result) /= equal(i)) error stop 7
        result = left(i) /= right(i)
        if (merge(1, 0, result) /= unequal(i)) error stop 8
        result = left(i) < right(i)
        if (merge(1, 0, result) /= less(i)) error stop 9
        result = left(i) <= right(i)
        if (merge(1, 0, result) /= less_equal(i)) error stop 10
        result = left(i) > right(i)
        if (merge(1, 0, result) /= greater(i)) error stop 11
        result = left(i) >= right(i)
        if (merge(1, 0, result) /= greater_equal(i)) error stop 12
    end do
end program intrinsic_relations
