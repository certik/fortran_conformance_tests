! rule: S10.2.1.3-013
! covers: different-lower-bounds rank-two noncontiguous-section reversed-section empty-array
! F2023 10.2.1.3 p6-p7.
program s10_2_1_3_013_valid
    implicit none
    integer :: source(-1:1), dest(5:7), storage(5), empty(0)
    integer :: matrix(-1:0, 3:5), copy(2, 3), i, j
    source = [2, 5, 9]
    dest = source
    if (dest(5) /= 2 .or. dest(6) /= 5 .or. dest(7) /= 9) error stop 'different-lower-bounds'
    storage = -1
    storage(1:5:2) = source
    if (any(storage /= [2, -1, 5, -1, 9])) error stop 'noncontiguous-section'
    dest = source(1:-1:-1)
    if (any(dest /= [9, 5, 2])) error stop 'reversed-section'
    do j = 3, 5
        do i = -1, 0
            matrix(i, j) = 100 * i + 10 * j
        end do
    end do
    copy = matrix
    if (copy(1, 1) /= -70 .or. copy(2, 1) /= 30) error stop 'rank-two-first-column'
    if (copy(1, 3) /= -50 .or. copy(2, 3) /= 50) error stop 'rank-two-last-column'
    empty = source(0:-1)
    if (size(empty) /= 0) error stop 'empty-array'
end program
