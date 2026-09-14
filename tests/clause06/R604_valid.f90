! rule: R604
! covers: literal-alternative named-alternative
! evidence: positive-control
program constant_alternatives
    implicit none
    integer, parameter :: chosen = 7
    integer :: literal_value, named_value
    data literal_value /5/
    data named_value /chosen/

    if (literal_value /= 2 + 3) error stop 1
    if (named_value /= 3 + 4) error stop 2
end program constant_alternatives
