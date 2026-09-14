! rule: S7.4.3.1-002
! covers: default-zero default-signed-zero
! evidence: effect
program p
    implicit none
    integer :: bare, positive, negative
    data bare, positive, negative /0, +0, -0/
    if (bare /= 1 - 1) error stop 1
    if (positive /= 1 - 1) error stop 2
    if (negative /= 1 - 1) error stop 3
    if (bare < 0) error stop 4
    if (bare > 0) error stop 5
    if (positive < 0) error stop 6
    if (positive > 0) error stop 7
    if (negative < 0) error stop 8
    if (negative > 0) error stop 9
end program
