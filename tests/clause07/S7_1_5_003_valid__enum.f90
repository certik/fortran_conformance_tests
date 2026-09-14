! rule: S7.1.5-003
! covers: enum-relations
! evidence: effect
! standard: f2023
program type_basics_enum_relations
    implicit none
    enum, bind(c) :: sample_enum
        enumerator :: low = 1, high = 3
    end enum
    type(sample_enum) :: left, right

    left = sample_enum(low)
    right = sample_enum(high)
    if (.not. (left < right)) error stop 1
    if (.not. (left == low)) error stop 2
    if (.not. (right == high)) error stop 3
    if (left == right) error stop 4
end program type_basics_enum_relations
