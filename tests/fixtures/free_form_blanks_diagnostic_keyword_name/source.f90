! rule: S6.3.2.2-003
! covers: keyword-name
! evidence: effect
program separator_name
  implicit none
  realx ! {error S6.3.2.2-003}
  x = 7.0
  if (x /= 7.0) stop 1
end program
