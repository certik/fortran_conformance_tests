! rule: S6.3.2.2-001
! covers: integer-interior
! evidence: effect
program token_integer
  implicit none
  integer :: value
  value = 1 2 ! {error S6.3.2.2-001}
  if (value /= 12) stop 1
end program
