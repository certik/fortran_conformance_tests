! rule: R611
! covers: six-digit-definition
! case: six-digits
program label_six_digits
    implicit none
    integer :: value
    value = 0
100000 value = value + 1 ! {error R611 six-digits}
    if (value /= 1) error stop 1
end program
