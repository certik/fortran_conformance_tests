! rule: S6.3.2.2-003
! covers: keyword-label
! evidence: effect
program separator_branch_label
  implicit none
  integer :: value
  value = 7
  goto10 ! {error S6.3.2.2-003}
  stop 2
10 continue
  if (value /= 7) stop 1
end program
