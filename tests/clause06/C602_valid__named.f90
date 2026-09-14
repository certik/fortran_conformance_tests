! rule: C602
! covers: integer-named
! evidence: positive-control
program integer_named_repeat
    implicit none
    integer, parameter :: repeats = 1
    ! Initialization conversion is permitted; the named entity is integer.
    integer, parameter :: converted = 1.0
    integer :: values(1), converted_values(1)
    data values /repeats * 7/
    data converted_values /converted * 7/

    if (values(1) /= 7) error stop 'integer-named-repeat'
    if (converted_values(1) /= 7) error stop 'converted-integer-repeat'
end program integer_named_repeat
