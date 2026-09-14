! rule: S6.3.2.2-001
! covers: name-interior
! evidence: effect
program token_name
  implicit none
  integer :: total_value
  total_ value = 7 ! {error S6.3.2.2-001}
  if (total_value /= 7) stop 1
end program
