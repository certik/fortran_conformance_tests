! rule: C1401
! covers: unnamed-program
    implicit none
    integer :: n
    n = 43
    if (n /= 43) error stop
end program
