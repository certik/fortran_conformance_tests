! rule: S10.2.1.3-006
! covers: initially-unallocated-scalar initially-unallocated-array after-deallocation empty-array
! F2023 10.2.1.3 p3.
program s10_2_1_3_006_valid
    implicit none
    integer, allocatable :: scalar, a(:), b(:, :)
    scalar = 17
    if (.not. allocated(scalar)) error stop 'scalar-allocation'
    if (scalar /= 17) error stop 'scalar-value'
    a = [2, 5, 9]
    if (.not. allocated(a)) error stop 'array-allocation'
    if (size(a) /= 3) error stop 'array-shape'
    if (any(a /= [2, 5, 9])) error stop 'array-value'
    a = [11, 13]
    if (.not. allocated(a)) error stop 'reallocation'
    if (size(a) /= 2) error stop 'reallocation-shape'
    if (any(a /= [11, 13])) error stop 'reallocation-value'
    a = [integer ::]
    if (.not. allocated(a)) error stop 'empty-allocation'
    if (size(a) /= 0) error stop 'empty-size'
    b = reshape([integer ::], [0, 3])
    if (.not. allocated(b)) error stop 'empty-rank-two-allocation'
    if (any(shape(b) /= [0, 3])) error stop 'empty-rank-two-shape'
end program
