! rule: R606
! covers: array-name
! evidence: positive-control
program array_named_constant
    implicit none
    integer, parameter :: numbers(3) = [2, 3, 5]

    if (size(numbers) /= 3) error stop 1
    if (numbers(1) /= 1 + 1) error stop 2
    if (numbers(2) /= 1 + 2) error stop 3
    if (numbers(3) /= 2 + 3) error stop 4
end program array_named_constant
