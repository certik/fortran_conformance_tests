! rule: S6.3.2.2-003
! covers: keyword-name
! evidence: positive-control
program separator_name
  implicit none
  real x
  x = 7.0
  if (x /= 7.0) stop 1
end program
