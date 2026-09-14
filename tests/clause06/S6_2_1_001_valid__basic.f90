! rule: S6.2.1-001
! covers: keyword name integer-literal comma equals double-colon
! evidence: positive-control
program token_basic_admission
    implicit none
    integer :: first, second

    first = 23
    second = 31
    if (first /= 23) error stop 1
    if (second /= 31) error stop 2
end program token_basic_admission
