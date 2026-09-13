! rule: S10.2.1.3-004
! covers: unallocated-array-rhs allocated-scalar-control
! evidence: positive-control
! F2023 10.2.1.3 p3. The unallocated/scalar violation is deliberately not executed.
program s10_2_1_3_004_valid
    implicit none
    integer, allocatable :: a(:), b(:, :)
    a = [2, 5, 9]
    if (.not. allocated(a)) error stop 'array-rhs-allocation'
    if (size(a) /= 3) error stop 'array-rhs-shape'
    if (any(a /= [2, 5, 9])) error stop 'array-rhs-value'
    deallocate(a)
    allocate(a(-1:1))
    a = 7
    if (lbound(a, 1) /= -1 .or. ubound(a, 1) /= 1) error stop 'allocated-scalar-bounds'
    if (any(a /= 7)) error stop 'allocated-scalar-control'
    b = reshape([1, 2, 3, 4, 5, 6], [2, 3])
    if (.not. allocated(b)) error stop 'rank-two-allocation'
    if (any(shape(b) /= [2, 3])) error stop 'rank-two-shape'
    if (b(2, 3) /= 6) error stop 'rank-two-value'
end program
