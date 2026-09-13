! rule: S10.2.1.3-011
! covers: whole-array-rhs section-rhs expression-rhs zero-extent-dimension existing-allocation-control
! F2023 10.2.1.3 p3, bullet 4; 16.9.119.
program s10_2_1_3_011_valid
    implicit none
    integer :: source(-4:-2)
    integer, allocatable :: a(:), empty(:)
    source = [2, 5, 9]
    a = source
    if (.not. allocated(a)) error stop 'whole-array-allocation'
    if (lbound(a, 1) /= -4 .or. ubound(a, 1) /= -2) error stop 'whole-array-bounds'
    if (any(a /= [2, 5, 9])) error stop 'whole-array-values'
    deallocate(a)
    a = source(:)
    if (.not. allocated(a)) error stop 'section-allocation'
    if (lbound(a, 1) /= 1 .or. ubound(a, 1) /= 3) error stop 'section-bounds'
    if (any(a /= [2, 5, 9])) error stop 'section-values'
    deallocate(a)
    a = source + 10
    if (lbound(a, 1) /= 1 .or. ubound(a, 1) /= 3) error stop 'expression-bounds'
    if (any(a /= [12, 15, 19])) error stop 'expression-values'
    deallocate(a)
    allocate(a(7:9))
    a = source
    if (lbound(a, 1) /= 7 .or. ubound(a, 1) /= 9) error stop 'existing-bounds'
    if (any(a /= [2, 5, 9])) error stop 'existing-values'
    deallocate(a)
    allocate(empty(-2:-3))
    a = empty
    if (.not. allocated(a)) error stop 'empty-allocation'
    if (size(a) /= 0) error stop 'empty-shape'
    if (lbound(a, 1) /= 1 .or. ubound(a, 1) /= 0) error stop 'empty-inquiry-bounds'
end program
