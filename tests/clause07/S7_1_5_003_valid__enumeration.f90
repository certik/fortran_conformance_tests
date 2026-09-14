! rule: S7.1.5-003
! covers: enumeration-relations
! evidence: effect
! standard: f2023
program type_basics_enumeration_relations
    implicit none
    enumeration type :: direction
        enumerator :: first, middle, last
    end enumeration type
    type(direction) :: left, right

    left = first
    right = direction(3)
    if (.not. (left < right)) error stop 1
    if (.not. (right == last)) error stop 2
    if (.not. (right > middle)) error stop 3
    if (left == right) error stop 4
end program type_basics_enumeration_relations
