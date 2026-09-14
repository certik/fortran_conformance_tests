! rule: S6.3.2.2-001
! covers: label-interior
! evidence: effect
program token_label
  implicit none
  integer :: value
  value = 7
  go to 10
  stop 2
1 0 continue ! {error S6.3.2.2-001}
  if (value /= 7) stop 1
end program
