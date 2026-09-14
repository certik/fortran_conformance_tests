! rule: S6.3.2.2-005
! covers: end-do
! evidence: positive-control
program do_spellings
  implicit none
  integer :: i, total
  total = 0
  do i = 1, 3
    total = total + i
  enddo
  if (total /= 6) stop 1
  do i = 1, 3
    total = total + i
  end do
  if (total /= 12) stop 2
end program
