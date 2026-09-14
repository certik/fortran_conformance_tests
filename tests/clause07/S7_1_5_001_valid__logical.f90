! rule: S7.1.5-001
! covers: logical-operation
! evidence: effect
program type_basics_logical_operation
    implicit none
    logical :: value = .false.
    logical :: result

    result = .not. value
    if (.not. result) error stop 1
end program type_basics_logical_operation
