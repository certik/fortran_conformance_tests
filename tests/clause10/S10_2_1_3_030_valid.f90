! rule: S10.2.1.3-030
! covers: initially-unallocated-destination dynamic-type kind-and-length-parameters nonunit-bounds empty-array independent-allocation
! F2023 10.2.1.3 p15(2).
program s10_2_1_3_030_valid
    implicit none
    integer, parameter :: dp = kind(0.0d0)
    type :: base
        integer :: n
    end type
    type, extends(base) :: child
        integer :: extra
    end type
    type :: packet
        class(base), allocatable :: object
        class(*), allocatable :: number
        integer, allocatable :: values(:)
        character(:), allocatable :: text
    end type
    type(packet) :: source, copy
    allocate(child :: source%object)
    select type (object => source%object)
    type is (child)
        object%n = 17
        object%extra = 31
    class default
        error stop 'source-type'
    end select
    source%number = 1.5_dp
    allocate(source%values(-2:0))
    source%values = [2, 5, 9]
    source%text = 'abc'
    copy = source
    if (.not. allocated(copy%object)) error stop 'object-allocation'
    if (.not. allocated(copy%number)) error stop 'number-allocation'
    if (.not. allocated(copy%values)) error stop 'array-allocation'
    if (.not. allocated(copy%text)) error stop 'text-allocation'
    if (.not. allocated(source%object)) error stop 'source-object-allocation'
    if (.not. allocated(source%number)) error stop 'source-number-allocation'
    if (.not. allocated(source%values)) error stop 'source-array-allocation'
    if (.not. allocated(source%text)) error stop 'source-text-allocation'
    select type (object => copy%object)
    type is (child)
        if (object%n /= 17 .or. object%extra /= 31) error stop 'dynamic-type-value'
    class default
        error stop 'dynamic-type'
    end select
    select type (number => copy%number)
    type is (real(kind=dp))
        if (number /= 1.5_dp) error stop 'kind-value'
    class default
        error stop 'kind-parameter'
    end select
    if (len(copy%text) /= 3 .or. copy%text /= 'abc') error stop 'length-parameter'
    if (size(copy%values) /= 3) error stop 'array-shape'
    if (lbound(copy%values, 1) /= -2 .or. ubound(copy%values, 1) /= 0) error stop 'nonunit-bounds'
    if (any(copy%values /= [2, 5, 9])) error stop 'array-value'
    copy%values(-2) = -17
    copy%text(1:1) = 'z'
    if (source%values(-2) /= 2 .or. source%text /= 'abc') error stop 'independent-allocation'
    deallocate(source%values)
    allocate(source%values(0))
    source%text = ''
    copy = source
    if (.not. allocated(copy%values)) error stop 'empty-array-allocation'
    if (.not. allocated(copy%text)) error stop 'empty-text-allocation'
    if (size(copy%values) /= 0 .or. len(copy%text) /= 0) error stop 'empty-metadata'
end program
