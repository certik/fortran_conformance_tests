! rule: S6.2.5-008
! covers: end-do-terminal
program label_do_end_do
    implicit none
    integer :: i, total
    total = 0
    do 10 i = 1, 3
        total = total + i
10  end do
    if (total /= 6) error stop 'do-body-total'
    if (i /= 4) error stop 'do-exit-index'
end program
