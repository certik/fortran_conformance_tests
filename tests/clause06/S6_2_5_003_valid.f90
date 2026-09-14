! rule: S6.2.5-003
! covers: padded-definition padded-reference decimal-identity
program label_zero_identity
    implicit none
    integer :: value
    value = 0
    go to 10
    error stop 1
00010 value = value + 1
    if (value == 1) go to 00020
    if (value == 2) go to 00100
    error stop 2
8   error stop 3
20  go to 010
100 if (value /= 2) error stop 4
end program
