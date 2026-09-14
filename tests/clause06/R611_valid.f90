! rule: R611
! covers: one-to-five-digits all-decimal-digits
! evidence: positive-control
program label_digits
    implicit none
    integer :: visits
    visits = 0
    go to 1
    error stop 1
1   visits = visits + 1
    go to 20
    error stop 2
20  visits = visits + 1
    go to 345
    error stop 3
345 visits = visits + 1
    go to 6078
    error stop 4
6078 visits = visits + 1
    go to 90009
    error stop 5
90009 visits = visits + 1
    if (visits /= 5) error stop 6
end program
