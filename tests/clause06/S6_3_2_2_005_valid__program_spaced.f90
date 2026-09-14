! rule: S6.3.2.2-005
! covers: end-program
! evidence: positive-control
program spaced_program
  implicit none
  integer :: value
  value = 9
  if (value /= 9) stop 1
end program spaced_program
