! rule: S6.3.2.2-001
! covers: boz-interior
! evidence: positive-control
program token_boz
  implicit none
  integer :: value
  data value / b'101' /
  if (value /= 5) stop 1
end program
