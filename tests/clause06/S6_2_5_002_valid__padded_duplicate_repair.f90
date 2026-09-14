! rule: S6.2.5-002
! covers: duplicate-leading-zeros
! evidence: positive-control
program label_padded_duplicate
    implicit none
    integer :: value
    value = 7
10  continue
00020 continue
    if (value /= 7) error stop 1
end program
