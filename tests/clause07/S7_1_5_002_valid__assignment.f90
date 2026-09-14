! rule: S7.1.5-002
! covers: intrinsic-assignment-not-operation
! evidence: positive-control
program type_basics_derived_assignment
    implicit none
    type :: item
        integer :: payload
    end type item
    type(item) :: left, right

    left%payload = 3
    right%payload = 19
    left = right
    if (left%payload /= 19) error stop 1
    if (right%payload /= 19) error stop 2
end program type_basics_derived_assignment
