! rule: S10.2.1.3-005
! covers: shape-change length-change dynamic-type-change polymorphic-kind-change unchanged-characteristics
! F2023 10.2.1.3 p3: inspect observable metadata, never old storage addresses.
program s10_2_1_3_005_valid
    implicit none
    integer, parameter :: sp = kind(0.0), dp = kind(0.0d0)
    integer, allocatable :: a(:, :)
    character(:), allocatable :: text
    class(*), allocatable :: value
    allocate(a(-1:0, 2:3))
    a = reshape([2, 3, 5, 7], [2, 2])
    if (any(lbound(a) /= [-1, 2])) error stop 'unchanged-characteristics'
    a = reshape([2, 3, 5, 7, 11, 13], [3, 2])
    if (.not. allocated(a)) error stop 'shape-allocation'
    if (any(shape(a) /= [3, 2])) error stop 'shape-change'
    if (a(3, 2) /= 13) error stop 'shape-value'
    text = 'ab'
    text = 'wxyz'
    if (.not. allocated(text)) error stop 'length-allocation'
    if (len(text) /= 4 .or. text /= 'wxyz') error stop 'length-change'
    value = 17
    value = 1.5_dp
    if (.not. allocated(value)) error stop 'dynamic-allocation'
    select type (value)
    type is (real(kind=dp))
        if (value /= 1.5_dp) error stop 'dynamic-type-value'
    class default
        error stop 'dynamic-type-change'
    end select
    value = 2.5_sp
    select type (value)
    type is (real(kind=sp))
        if (value /= 2.5_sp) error stop 'polymorphic-kind-value'
    class default
        error stop 'polymorphic-kind-change'
    end select
end program
