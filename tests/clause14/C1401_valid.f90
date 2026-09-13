! rule: C1401
! covers: matching-name different-case
program c1401_valid
    implicit none
    integer :: n
    n = 17
    if (n /= 17) error stop
end program C1401_VALID
