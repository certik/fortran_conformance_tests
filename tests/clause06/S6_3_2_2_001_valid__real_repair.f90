! rule: S6.3.2.2-001
! covers: real-interior
! evidence: positive-control
program token_real
  implicit none
  real :: value
  value = 1.0E+2
  if (value /= 100.0) stop 1
end program
