! rule: S6.2.1-001
! covers: colon
! evidence: positive-control
program token_colon_admission
    implicit none
    integer :: values(3)

    values = 0
    values(2:3) = 7
    if (values(1) /= 0) error stop 1
    if (values(2) /= 7) error stop 2
    if (values(3) /= 7) error stop 3
end program token_colon_admission
