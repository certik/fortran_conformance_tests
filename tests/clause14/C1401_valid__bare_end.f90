! rule: C1401
! covers: named-program-bare-end
program c1401_bare_end
    implicit none
    integer :: n
    n = 23
    if (n /= 23) error stop
end
