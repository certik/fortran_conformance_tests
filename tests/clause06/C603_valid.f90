! rule: C603
! covers: nonzero-at-each-position
! evidence: positive-control
program label_nonzero_positions
    implicit none
    integer :: visits
    visits = 0
    go to 10000
    error stop 1
10000 visits = visits + 1
    go to 01000
    error stop 2
01000 visits = visits + 1
    go to 00100
    error stop 3
00100 visits = visits + 1
    go to 00010
    error stop 4
00010 visits = visits + 1
    go to 00001
    error stop 5
00001 visits = visits + 1
    if (visits /= 5) error stop 6
end program
