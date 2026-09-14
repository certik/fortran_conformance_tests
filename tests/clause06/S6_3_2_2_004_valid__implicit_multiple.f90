! rule: S6.3.2.2-004
! covers: implicit-none
! evidence: positive-control
program multiple_keyword_blanks
  implicit   none
  integer :: value
  value = 7
  if (value /= 7) stop 1
end program
