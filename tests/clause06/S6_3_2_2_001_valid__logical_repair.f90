! rule: S6.3.2.2-001
! covers: logical-interior
! evidence: positive-control
program token_logical
  implicit none
  logical :: flag
  flag = .true.
  if (.not. flag) stop 1
end program
