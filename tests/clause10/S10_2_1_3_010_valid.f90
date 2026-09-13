! rule: S10.2.1.3-010
! covers: initial-allocation changed-shape same-size-different-shape zero-extent-dimension section-rhs
! F2023 10.2.1.3 p3, bullet 4.
program s10_2_1_3_010_valid
    implicit none
    integer, allocatable :: a(:, :)
    integer :: source(3, 4), i, j
    a = reshape([2, 3, 5, 7, 11, 13], [2, 3])
    if (.not. allocated(a)) error stop 'initial-allocation'
    if (any(shape(a) /= [2, 3])) error stop 'initial-shape'
    if (a(2, 3) /= 13) error stop 'initial-value'
    a = reshape([2, 3, 5, 7, 11, 13], [3, 2])
    if (any(shape(a) /= [3, 2])) error stop 'same-size-different-shape'
    if (a(3, 2) /= 13) error stop 'changed-value'
    do j = 1, 4
        do i = 1, 3
            source(i, j) = 10 * j + i
        end do
    end do
    a = source(1:3:2, 2:4)
    if (any(shape(a) /= [2, 3])) error stop 'section-shape'
    if (a(1, 1) /= 21 .or. a(2, 3) /= 43) error stop 'section-value'
    a = reshape([integer ::], [0, 4])
    if (.not. allocated(a)) error stop 'empty-allocation'
    if (any(shape(a) /= [0, 4])) error stop 'empty-shape'
end program
