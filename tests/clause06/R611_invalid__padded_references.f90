! rule: R611
! covers: zero-padded-overlength-reference
! case: branch
program label_padded_branch
    implicit none
    go to 000010 ! {error R611 branch}
    error stop 1
10  continue
end program
! case: format
program label_padded_format
    implicit none
    character(1) :: text
    write(text, fmt=000010) 1 ! {error R611 format}
    if (text /= '1') error stop 1
10  format(i1)
end program
! case: do-terminal
program label_padded_do
    implicit none
    integer :: i, total
    total = 0
    do 000010 i = 1, 3 ! {error R611 do-terminal}
        total = total + i
10  continue
    if (total /= 6 .or. i /= 4) error stop 1
end program
