! rule: C602
! covers: integer-literal
! evidence: positive-control
program integer_literal_repeat
    implicit none
    integer :: values(2)
    data values /2 * 7/

    if (values(1) /= 7) error stop 1
    if (values(2) /= 7) error stop 2
end program integer_literal_repeat
