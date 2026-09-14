! rule: R611
! covers: nondigit-reference
! case: sign
program label_sign
    implicit none
    go to +10 ! {error R611 sign}
    error stop 1
10  continue
end program
! case: decimal-point
program label_decimal
    implicit none
    go to 10.0 ! {error R611 decimal-point}
    error stop 1
10  continue
end program
! case: exponent
program label_exponent
    implicit none
    go to 1e1 ! {error R611 exponent}
    error stop 1
10  continue
end program
! case: kind-suffix
program label_kind
    implicit none
    go to 10_4 ! {error R611 kind-suffix}
    error stop 1
10  continue
end program
! case: letter
program label_letter
    implicit none
    go to 10a ! {error R611 letter}
    error stop 1
10  continue
end program
