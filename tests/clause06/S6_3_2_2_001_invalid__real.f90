! rule: S6.3.2.2-001
! covers: real-interior
! evidence: effect
program token_real
  implicit none
  real :: value
  value = 1.0 E+2 ! {error S6.3.2.2-001}
  if (value /= 100.0) stop 1
end program
