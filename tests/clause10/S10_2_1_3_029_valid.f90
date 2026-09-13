! rule: S10.2.1.3-029
! covers: allocated-to-unallocated both-unallocated allocated-to-allocated
! F2023 10.2.1.3 p15(1)-(2). No reads through a deallocated component.
program s10_2_1_3_029_valid
    implicit none
    type :: packet
        integer :: tag
        integer, allocatable :: values(:)
    end type
    type(packet) :: source, copy
    source%tag = 17
    allocate(copy%values(2))
    copy%values = [2, 5]
    copy = source
    if (allocated(copy%values)) error stop 'allocated-to-unallocated'
    if (copy%tag /= 17) error stop 'ordinary-component'
    copy = source
    if (allocated(copy%values)) error stop 'both-unallocated'
    allocate(source%values(-1:1))
    source%values = [7, 11, 13]
    copy = source
    if (.not. allocated(copy%values)) error stop 'allocated-source'
    if (.not. allocated(source%values)) error stop 'source-allocation-preserved'
    if (size(copy%values) /= 3) error stop 'copy-shape'
    if (lbound(copy%values, 1) /= -1 .or. ubound(copy%values, 1) /= 1) error stop 'copy-bounds'
    if (any(copy%values /= [7, 11, 13])) error stop 'allocated-source-value'
    copy%values(-1) = -19
    if (source%values(-1) /= 7) error stop 'independent-allocation'
    source%values = [17, 23, 31]
    copy = source
    if (.not. allocated(copy%values)) error stop 'allocated-to-allocated'
    if (size(copy%values) /= 3) error stop 'replacement-shape'
    if (any(copy%values /= [17, 23, 31])) error stop 'replacement-value'
end program
