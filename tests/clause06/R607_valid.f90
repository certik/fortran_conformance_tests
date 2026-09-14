! rule: R607
! covers: literal-integer named-integer
! evidence: positive-control
program integer_constant_alternatives
    implicit none
    integer, parameter :: repeats = 1 + 2
    integer :: literal_values(3), named_values(4)
    data literal_values /2 * 5, 9/
    data named_values /repeats * 7, 12/

    if (literal_values(1) /= 5) error stop 1
    if (literal_values(2) /= 5) error stop 2
    if (literal_values(3) /= 9) error stop 3
    if (named_values(1) /= 7) error stop 4
    if (named_values(2) /= 7) error stop 5
    if (named_values(3) /= 7) error stop 6
    if (named_values(4) /= 12) error stop 7
end program integer_constant_alternatives
