! rule: S6.2.6-001
! covers: slash
! evidence: positive-control
program delimiter_slash_admission
    implicit none
    integer :: first, second
    data first, second /11, 17/

    if (first /= 11) error stop 1
    if (second /= 17) error stop 2
end program delimiter_slash_admission
