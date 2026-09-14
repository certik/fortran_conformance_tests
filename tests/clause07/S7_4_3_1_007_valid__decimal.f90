! rule: S7.4.3.1-007
! covers: all-digits positional-value leading-zero-decimal
! evidence: effect
program p
    implicit none
    integer :: values(10), i, positional, padded
    data values /0, 1, 2, 3, 4, 5, 6, 7, 8, 9/
    data positional, padded /12345, 00089/
    if (size(values) /= 10) error stop 1
    if (lbound(values, 1) /= 1) error stop 2
    if (ubound(values, 1) /= 10) error stop 3
    do i = 1, 10
        if (values(i) /= i - 1) error stop 4
    end do
    if (positional /= 10000 + 2000 + 300 + 40 + 5) error stop 5
    if (padded /= 8 * 10 + 9) error stop 6
end program
