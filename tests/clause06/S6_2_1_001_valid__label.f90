! rule: S6.2.1-001
! covers: statement-label
! evidence: positive-control
program token_label_admission
    implicit none
    integer :: value

    value = 0
    go to 10
    error stop 1
10  value = 7
    if (value /= 7) error stop 2
end program token_label_admission
