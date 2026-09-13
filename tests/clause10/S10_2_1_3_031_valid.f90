! rule: S10.2.1.3-031
! covers: declared-type-binding matching-interface allocated-destination-at-assignment controlled-value-effect
! F2023 10.2.1.3 p15(2).
module s10_2_1_3_031_m
    implicit none
    integer :: calls = 0, fresh = 0
    type :: item
        integer :: value = -1000
    contains
        procedure :: assign_item
        generic :: assignment(=) => assign_item
    end type
    type :: packet
        type(item), allocatable :: object
    end type
contains
    subroutine assign_item(left, right)
        class(item), intent(inout) :: left
        class(item), intent(in) :: right
        calls = calls + 1
        ! Default initialization makes the allocation step observable at binding entry.
        if (left%value == -1000) fresh = fresh + 1
        left%value = right%value + 100
    end subroutine
end module
program s10_2_1_3_031_valid
    use s10_2_1_3_031_m
    implicit none
    type(packet) :: source, copy
    allocate(source%object)
    source%object%value = 7
    copy = source
    if (.not. allocated(copy%object)) error stop 'component-allocation'
    if (copy%object%value /= 107) error stop 'defined-assignment'
    if (calls /= 1 .or. fresh /= 1) error stop 'first-binding-entry'
    source%object%value = 11
    copy = source
    if (.not. allocated(copy%object)) error stop 'replacement-allocation'
    if (copy%object%value /= 111) error stop 'replacement-defined-assignment'
    if (calls /= 2 .or. fresh /= 2) error stop 'replacement-binding-entry'
    if (.not. allocated(source%object)) error stop 'source-allocation-preserved'
    if (source%object%value /= 11) error stop 'source-unchanged'
end program
