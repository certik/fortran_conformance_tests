! rule: S6.3.2.2-003
! covers: label-keyword
! evidence: positive-control
program separator_statement_label
  implicit none
  integer :: value
  value = 7
  go to 10
  stop 2
10 continue
  if (value /= 7) stop 1
end program
