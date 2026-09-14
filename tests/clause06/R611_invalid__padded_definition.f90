! rule: R611
! covers: zero-padded-overlength-definition
! case: six-digits-value-one
program label_padded_definition
    implicit none
    integer :: value
    value = 0
000001 value = value + 1 ! {error R611 six-digits-value-one}
    if (value /= 1) error stop 1
end program
