! rule: R608
! covers: power-op
! evidence: positive-control
program intrinsic_power
    implicit none
    integer :: base, exponent, result

    base = 3
    exponent = 4
    result = base ** exponent
    if (result /= 81) error stop 1
    exponent = 0
    result = base ** exponent
    if (result /= 1) error stop 2
end program intrinsic_power
