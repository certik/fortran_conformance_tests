! rule: S6.3.2.2-001
! covers: double-colon-interior
! evidence: positive-control
program token_double_colon
  implicit none
  integer :: value
  value = 7
  if (value /= 7) stop 1
end program
