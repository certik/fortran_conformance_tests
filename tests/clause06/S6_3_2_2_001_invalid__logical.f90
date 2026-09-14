! rule: S6.3.2.2-001
! covers: logical-interior
! evidence: effect
program token_logical
  implicit none
  logical :: flag
  flag = .tr ue. ! {error S6.3.2.2-001}
  if (.not. flag) stop 1
end program
