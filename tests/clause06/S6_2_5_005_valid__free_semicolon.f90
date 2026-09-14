! rule: S6.2.5-005
! covers: free-semicolon
! evidence: positive-control
program label_free_semicolon
    implicit none
    integer :: value
    value = 0
    go to 10
    value = 99; 10 value = value + 1
    if (value /= 1) error stop 1
end program
