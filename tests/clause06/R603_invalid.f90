! rule: R603
! covers: initial-letter
! Free-form source; each case contains one malformed name in a declaration.
! case: initial-digit
program bad_initial_digit
    implicit none
    integer :: 1name ! {error R603 initial-digit}
end program bad_initial_digit
! case: initial-underscore
program bad_initial_underscore
    implicit none
    integer :: _name ! {error R603 initial-underscore}
end program bad_initial_underscore
! case: initial-special
program bad_initial_special
    implicit none
    integer :: @name ! {error R603 initial-special}
end program bad_initial_special
