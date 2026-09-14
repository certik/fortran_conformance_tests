! rule: R605
! covers: complex-literal
! evidence: positive-control
program complex_literal_alternative
    implicit none
    complex :: value
    data value /(2.0, 3.0)/

    if (real(value) /= real(1 + 1)) error stop 1
    if (aimag(value) /= real(1 + 2)) error stop 2
end program complex_literal_alternative
