! rule: S6.3.2.2-004
! covers: implicit-none
! evidence: positive-control
program required_keyword_separator
  implicit none
  integer :: value
  value = 7
  if (value /= 7) stop 1
end program
