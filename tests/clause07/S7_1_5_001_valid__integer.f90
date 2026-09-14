! rule: S7.1.5-001
! covers: integer-operation
! evidence: effect
program type_basics_integer_operation
    implicit none
    integer :: left = 2, right = 3
    if (left + right /= 5) error stop 1
end program type_basics_integer_operation
