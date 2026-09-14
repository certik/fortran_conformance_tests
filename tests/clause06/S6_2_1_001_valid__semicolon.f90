! rule: S6.2.1-001
! covers: semicolon
! evidence: positive-control
program token_semicolon_admission
    implicit none
    integer :: value

    value = 2; value = value + 3
    if (value /= 5) error stop 1
end program token_semicolon_admission
