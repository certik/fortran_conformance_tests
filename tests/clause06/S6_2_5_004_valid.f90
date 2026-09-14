! rule: S6.2.5-004
! covers: range-endpoints decimal-width-boundaries beyond-signed-16-bit beyond-unsigned-16-bit
program label_value_boundaries
    implicit none
    integer :: visits
    visits = 0
    go to 1
    error stop 1
1   visits = visits + 1
    go to 9
    error stop 2
9   visits = visits + 1
    go to 10
    error stop 3
10  visits = visits + 1
    go to 99
    error stop 4
99  visits = visits + 1
    go to 100
    error stop 5
100 visits = visits + 1
    go to 999
    error stop 6
999 visits = visits + 1
    go to 1000
    error stop 7
1000 visits = visits + 1
    go to 9999
    error stop 8
9999 visits = visits + 1
    go to 10000
    error stop 9
10000 visits = visits + 1
    go to 32767
    error stop 10
32767 visits = visits + 1
    go to 32768
    error stop 11
32768 visits = visits + 1
    go to 65535
    error stop 12
65535 visits = visits + 1
    go to 65536
    error stop 13
65536 visits = visits + 1
    go to 99999
    error stop 14
99999 visits = visits + 1
    if (visits /= 14) error stop 15
end program
