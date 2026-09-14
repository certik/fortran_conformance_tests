! rule: R601
! covers: digit-alternative
! evidence: positive-control
program alphadigits
    implicit none
    integer :: n0, n1, n2, n3, n4, n5, n6, n7, n8, n9

    n0 = 10
    n1 = 11
    n2 = 12
    n3 = 13
    n4 = 14
    n5 = 15
    n6 = 16
    n7 = 17
    n8 = 18
    n9 = 19
    if (n0 /= 10) error stop 1
    if (n1 /= 11) error stop 2
    if (n2 /= 12) error stop 3
    if (n3 /= 13) error stop 4
    if (n4 /= 14) error stop 5
    if (n5 /= 15) error stop 6
    if (n6 /= 16) error stop 7
    if (n7 /= 17) error stop 8
    if (n8 /= 18) error stop 9
    if (n9 /= 19) error stop 10
end program alphadigits
