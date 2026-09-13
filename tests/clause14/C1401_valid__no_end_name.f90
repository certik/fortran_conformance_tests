! rule: C1401
! covers: named-program-unnamed-end
program c1401_no_end_name
    implicit none
    integer :: n
    n = 31
    if (n /= 31) error stop
end program
