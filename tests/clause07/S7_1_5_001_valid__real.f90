! rule: S7.1.5-001
! covers: real-operation
! evidence: effect
program type_basics_real_operation
    implicit none
    real :: value = 0.0
    if (+value /= 0.0) error stop 1
end program type_basics_real_operation
