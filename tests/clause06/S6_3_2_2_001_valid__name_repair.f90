! rule: S6.3.2.2-001
! covers: name-interior
! evidence: positive-control
program token_name
  implicit none
  integer :: total_value
  total_value = 7
  if (total_value /= 7) stop 1
end program
