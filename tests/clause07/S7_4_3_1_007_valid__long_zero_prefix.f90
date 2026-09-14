! rule: S7.4.3.1-007
! covers: long-leading-zero-small
! evidence: effect
program p
    implicit none
    integer :: nonzero, zero
    data nonzero /000000000000000000000000000000000000000000000000000000000000000089/
    data zero /0000000000000000000000000000000000000000000000000000000000000000/
    if (nonzero /= 8 * 10 + 9) error stop 1
    if (zero /= 1 - 1) error stop 2
end program
