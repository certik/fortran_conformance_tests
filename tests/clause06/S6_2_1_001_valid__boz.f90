! rule: S6.2.1-001
! covers: boz-literal
! evidence: positive-control
! C7119 and 8.6.7 p11 admit this short BOZ value for integer DATA initialization.
program token_boz_admission
    implicit none
    integer :: value
    data value /B'101'/

    if (value /= 5) error stop 1
end program token_boz_admission
