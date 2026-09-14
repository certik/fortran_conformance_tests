! rule: S6.2.1-001
! covers: arrow
! evidence: positive-control
program token_arrow_admission
    implicit none
    integer, target :: value
    integer, pointer :: link

    value = 13
    link => value
    if (link /= 13) error stop 1
    link = 17
    if (value /= 17) error stop 2
end program token_arrow_admission
