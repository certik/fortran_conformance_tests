! rule: S6.2.1-001
! covers: logical-literal
! evidence: positive-control
program token_logical_admission
    implicit none
    logical :: value

    value = .true.
    if (.not. value) error stop 1
    value = .false.
    if (value) error stop 2
end program token_logical_admission
