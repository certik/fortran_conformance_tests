! rule: S6.2.5-002
! covers: duplicate-spelling
! case: repeated
program label_duplicate
    implicit none
    integer :: value
    value = 7
10  continue
10  continue ! {error S6.2.5-002 repeated}
    if (value /= 7) error stop 1
end program
