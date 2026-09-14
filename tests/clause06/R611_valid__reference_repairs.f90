! rule: R611
! covers: zero-padded-overlength-reference nondigit-reference
! evidence: positive-control
program label_reference_repairs
    implicit none
    integer :: i, total
    character(1) :: text
    go to 10
    error stop 'branch-reference'
10  total = 0
    do 00020 i = 1, 3
        total = total + i
20  continue
    if (total /= 6) error stop 'do-body-total'
    if (i /= 4) error stop 'do-exit-index'
    write(text, fmt=00100) total
    if (text /= '6') error stop 'padded-format-reference'
    go to 00030
    error stop 'padded-branch-reference'
30  continue
100 format(i1)
end program
