! rule: S6.3.2.2-001
! covers: operator-interior
! evidence: positive-control
program token_operator
  implicit none
  integer :: value
  value = 2 ** 3
  if (value /= 8) stop 1
end program
