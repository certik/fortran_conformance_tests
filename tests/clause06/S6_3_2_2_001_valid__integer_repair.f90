! rule: S6.3.2.2-001
! covers: integer-interior
! evidence: positive-control
program token_integer
  implicit none
  integer :: value
  value = 12
  if (value /= 12) stop 1
end program
