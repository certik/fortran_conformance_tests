! rule: S6.2.1-001
! covers: real-literal
! evidence: positive-control
program token_real_admission
    implicit none
    real :: value

    value = 2.0
    if (value /= 2.0) error stop 1
end program token_real_admission
