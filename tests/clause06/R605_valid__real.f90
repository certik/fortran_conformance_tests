! rule: R605
! covers: real-literal
! evidence: positive-control
program real_literal_alternative
    implicit none
    real :: value
    data value /6.0/

    if (value /= real(2 * 3)) error stop 1
end program real_literal_alternative
