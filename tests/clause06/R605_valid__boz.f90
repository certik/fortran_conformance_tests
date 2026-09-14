! rule: R605
! covers: boz-literal
! evidence: positive-control
! C7119 and 8.6.7 p11 permit a BOZ DATA value for an integer object.
program boz_literal_alternative
    implicit none
    integer :: value
    data value /Z'2A'/

    if (value /= 6 * 7) error stop 1
end program boz_literal_alternative
