! rule: S10.2.1.3-029
! covers: matching-characteristics allocated-to-allocated
! F2023 10.2.1.3 p15(1), with 7.5.6.2-7.5.6.3.
! Only the old destination's unique value is counted; RHS/default-initialized temporaries cannot match it.
module s10_2_1_3_029_m
    implicit none
    integer :: expected_old = 0, finalized_old = 0
    type :: item
        integer :: value = -1
    contains
        final :: finish
    end type
    type :: packet
        type(item), allocatable :: object
    end type
contains
    subroutine finish(object)
        type(item), intent(in) :: object
        if (object%value == expected_old) finalized_old = finalized_old + 1
    end subroutine
end module
program s10_2_1_3_029_finalization
    use s10_2_1_3_029_m
    implicit none
    type(packet) :: source, copy
    allocate(source%object, copy%object)
    source%object%value = 7
    copy%object%value = 101
    expected_old = 101
    copy = source
    if (finalized_old /= 1) error stop 'matching-characteristics-finalization'
    if (.not. allocated(copy%object)) error stop 'replacement-allocation'
    if (copy%object%value /= 7) error stop 'replacement-value'
    copy%object%value = 103
    expected_old = 103
    finalized_old = 0
    copy = source
    if (finalized_old /= 1) error stop 'repeated-finalization'
    if (copy%object%value /= 7 .or. source%object%value /= 7) error stop 'repeated-value'
end program
