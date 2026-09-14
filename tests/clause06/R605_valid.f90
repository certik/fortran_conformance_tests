! rule: R605
! covers: integer-literal
! evidence: positive-control
program integer_literal_alternative
    implicit none
    integer :: value
    data value /42/

    if (value /= 6 * 7) error stop 1
end program integer_literal_alternative
