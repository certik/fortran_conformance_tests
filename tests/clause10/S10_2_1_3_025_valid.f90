! rule: S10.2.1.3-025
! covers: scalar-component array-component matching-binding nonmatching-binding-control
! F2023 10.2.1.3 p15-p16. Only the total callback count, not component order, is checked.
module s10_2_1_3_025_m
    implicit none
    integer :: calls = 0, wrong_calls = 0
    type :: item
        integer :: value = 0
    contains
        procedure :: assign_item
        generic :: assignment(=) => assign_item
    end type
    type :: other_item
        integer :: value = 0
    contains
        procedure :: assign_integer
        generic :: assignment(=) => assign_integer
    end type
    type :: packet
        type(item) :: scalar, values(2)
        type(other_item) :: other
    end type
contains
    impure elemental subroutine assign_item(left, right)
        class(item), intent(inout) :: left
        class(item), intent(in) :: right
        calls = calls + 1
        left%value = right%value + 100
    end subroutine
    subroutine assign_integer(left, right)
        class(other_item), intent(inout) :: left
        integer, intent(in) :: right
        wrong_calls = wrong_calls + 1
        left%value = right + 1000
    end subroutine
end module
program s10_2_1_3_025_valid
    use s10_2_1_3_025_m
    implicit none
    type(packet) :: source, copy
    source%scalar%value = 2
    source%values(1)%value = 3
    source%values(2)%value = 5
    source%other%value = 17
    copy = source
    if (copy%scalar%value /= 102) error stop 'scalar-defined-assignment'
    if (copy%values(1)%value /= 103 .or. copy%values(2)%value /= 105) error stop 'array-defined-assignment'
    if (calls /= 3) error stop 'matching-binding-count'
    if (copy%other%value /= 17 .or. wrong_calls /= 0) error stop 'nonmatching-binding-control'
    if (source%scalar%value /= 2) error stop 'source-unchanged'
end program
