! rule: S7.1.5-001
! covers: complex-operation
! evidence: effect
program type_basics_complex_operation
    implicit none
    complex :: value = (0.0, 0.0)
    if (+value /= (0.0, 0.0)) error stop 1
end program type_basics_complex_operation
