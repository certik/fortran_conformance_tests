! rule: S6.3.2.6-001
! covers: after-semicolon
! evidence: positive-control
program semicolon_label
  implicit none
  integer :: value
  value = 0
  go to 30; value = 99; 30 value = value + 7
  if (value /= 7) error stop 1
end program
