! rule: S10.2.1.3-009
! covers: character-length-change polymorphic-type-change nonunit-lower-bounds zero-extent-control
! F2023 10.2.1.3 p3, bullet 3.
program s10_2_1_3_009_valid
    implicit none
    integer, parameter :: dp = kind(0.0d0)
    character(:), allocatable :: text(:), empty(:)
    class(*), allocatable :: values(:)
    allocate(character(2) :: text(-2:0))
    text = 'ab'
    text = 'wxyz'
    if (.not. allocated(text)) error stop 'character-allocation'
    if (len(text) /= 4) error stop 'character-length'
    if (lbound(text, 1) /= -2 .or. ubound(text, 1) /= 0) error stop 'character-bounds'
    if (any(text /= 'wxyz')) error stop 'character-values'
    allocate(character(1) :: empty(1:0))
    empty = 'long'
    if (.not. allocated(empty)) error stop 'empty-allocation'
    if (size(empty) /= 0 .or. len(empty) /= 4) error stop 'empty-metadata'
    allocate(integer :: values(-1:1))
    values = 2.5_dp
    if (.not. allocated(values)) error stop 'polymorphic-allocation'
    if (lbound(values, 1) /= -1 .or. ubound(values, 1) /= 1) error stop 'polymorphic-bounds'
    select type (values)
    type is (real(kind=dp))
        if (any(values /= 2.5_dp)) error stop 'polymorphic-values'
    class default
        error stop 'polymorphic-type'
    end select
end program
