! rule: S6.3.2.2-003
! covers: label-name
! evidence: positive-control
program separator_do_label
  implicit none
  integer :: i, total
  total = 0
  do 10 i = 1, 3
    total = total + i
10 end do
  if (total /= 6) stop 1
end program
