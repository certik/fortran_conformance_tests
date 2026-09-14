! rule: R601
! covers: letter-alternative
! evidence: positive-control
program alphaletters
    implicit none
    integer :: nA, nz

    nA = 7
    nz = 13
    if (nA /= 7) error stop 1
    if (nz /= 13) error stop 2
end program alphaletters
