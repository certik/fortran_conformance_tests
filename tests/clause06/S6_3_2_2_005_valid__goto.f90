! rule: S6.3.2.2-005
! covers: go-to
! evidence: positive-control
program goto_spellings
  implicit none
  integer :: value
  value = 7
  goto 10
  stop 1
10 continue
  if (value /= 7) stop 2
  value = 9
  go to 20
  stop 3
20 continue
  if (value /= 9) stop 4
end program
