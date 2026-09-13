! rule: S10.2.1.3-032
! covers: intrinsic-component-type derived-component-type extended-dynamic-type dynamic-only-binding-control nested-allocatable-component
! F2023 10.2.1.3 p15(2): dispatch depends on the component's declared type.
module s10_2_1_3_032_m
    implicit none
    integer :: wrong_calls = 0
    type :: base
        integer :: n
    end type
    type, extends(base) :: child
        integer :: extra
        integer, allocatable :: nested(:)
    contains
        procedure :: assign_child
        generic :: assignment(=) => assign_child
    end type
    type :: packet
        class(base), allocatable :: object
        integer, allocatable :: values(:)
    end type
contains
    subroutine assign_child(left, right)
        class(child), intent(inout) :: left
        class(child), intent(in) :: right
        wrong_calls = wrong_calls + 1
        left%n = right%n + 1000
        left%extra = right%extra + 1000
    end subroutine
end module
program s10_2_1_3_032_valid
    use s10_2_1_3_032_m
    implicit none
    type(packet) :: source, copy
    allocate(child :: source%object)
    select type (object => source%object)
    type is (child)
        object%n = 17
        object%extra = 31
        object%nested = [2, 5, 9]
    class default
        error stop 'source-type'
    end select
    source%values = [11, 13]
    copy = source
    if (.not. allocated(copy%object)) error stop 'object-allocation'
    if (.not. allocated(copy%values)) error stop 'intrinsic-allocation'
    if (.not. allocated(source%object)) error stop 'source-object-allocation'
    if (.not. allocated(source%values)) error stop 'source-intrinsic-allocation'
    if (size(copy%values) /= 2) error stop 'intrinsic-shape'
    if (any(copy%values /= [11, 13])) error stop 'intrinsic-component-type'
    select type (object => copy%object)
    type is (child)
        if (object%n /= 17 .or. object%extra /= 31) error stop 'extended-dynamic-type'
        if (.not. allocated(object%nested)) error stop 'nested-allocation'
        if (size(object%nested) /= 3) error stop 'nested-shape'
        if (any(object%nested /= [2, 5, 9])) error stop 'nested-value'
        object%nested(1) = -19
    class default
        error stop 'destination-type'
    end select
    if (wrong_calls /= 0) error stop 'dynamic-only-binding-control'
    select type (object => source%object)
    type is (child)
        if (.not. allocated(object%nested)) error stop 'source-nested-allocation'
        if (size(object%nested) /= 3) error stop 'source-nested-shape'
        if (object%nested(1) /= 2) error stop 'nested-independent-storage'
    class default
        error stop 'source-type-unchanged'
    end select
end program
