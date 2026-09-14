! rule: C603
! covers: nonzero-branch-reference nonzero-format-reference nonzero-do-reference
! evidence: positive-control
program label_nonzero_references
    implicit none
    integer :: i, total
    character(1) :: text
    go to 00001
    error stop 'padded-branch-reference'
1   total = 0
    do 00002 i = 1, 3
        total = total + i
2   continue
    write(text, fmt=00003) total
    if (total /= 6) error stop 'do-body-total'
    if (i /= 4) error stop 'do-exit-index'
    if (text /= '6') error stop 'padded-format-reference'
3   format(i1)
end program
