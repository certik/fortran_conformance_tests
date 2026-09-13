! rule: S10.2.1.3-027
! covers: allocated-scalar-component allocated-array-component per-image-values
! requires: coarray
! F2023 10.2.1.3 p15. This also has a conforming single-image execution.
program s10_2_1_3_027_valid
    implicit none
    type :: packet
        integer, allocatable :: scalar[:]
        integer, allocatable :: values(:)[:]
    end type
    type(packet), save :: source, copy
    integer :: image
    image = this_image()
    allocate(source%scalar[*])
    allocate(copy%scalar[*])
    allocate(source%values(-1:1)[*])
    allocate(copy%values(4:6)[*])
    source%scalar = 17 * image
    source%values = [2 * image, 3 * image, 5 * image]
    copy%scalar = -1
    copy%values = -1
    sync all
    ! Direct component assignment controls for the component-wise outer assignment.
    copy%values = source%values
    if (lbound(copy%values, 1) /= 4 .or. ubound(copy%values, 1) /= 6) error stop 'direct-component-bounds'
    copy%values = -1
    copy = source
    if (.not. allocated(copy%scalar)) error stop 'scalar-allocation'
    if (.not. allocated(copy%values)) error stop 'array-allocation'
    if (copy%scalar /= 17 * image) error stop 'allocated-scalar-component'
    if (lbound(copy%values, 1) /= 4 .or. ubound(copy%values, 1) /= 6) error stop 'destination-bounds'
    if (any(copy%values /= [2 * image, 3 * image, 5 * image])) error stop 'allocated-array-component'
    copy%values(4) = -19
    if (source%values(-1) /= 2 * image) error stop 'independent-coarray-values'
    deallocate(source%scalar)
    deallocate(copy%scalar)
    deallocate(source%values)
    deallocate(copy%values)
end program
