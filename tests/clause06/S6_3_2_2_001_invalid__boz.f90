! rule: S6.3.2.2-001
! covers: boz-interior
! evidence: effect
program token_boz
  implicit none
  integer :: value
  data value / b'1 01' / ! {error S6.3.2.2-001}
  if (value /= 5) stop 1
end program
