! rule: R711
! covers: one-digit multiple-digits leading-zero
! evidence: positive-control
program p
    implicit none
    integer :: a, b, c
    data a, b, c /7, 12345, 00089/
    if (a /= 3 + 4) error stop 1
    if (b /= 12000 + 345) error stop 2
    if (c /= 80 + 9) error stop 3
end program
