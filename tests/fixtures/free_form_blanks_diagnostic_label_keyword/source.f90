! rule: S6.3.2.2-003
! covers: label-keyword
! evidence: effect
program separator_statement_label
  implicit none
  integer :: value
  value = 7
  go to 10
  stop 2
10continue ! {error S6.3.2.2-003}
  if (value /= 7) stop 1
end program
