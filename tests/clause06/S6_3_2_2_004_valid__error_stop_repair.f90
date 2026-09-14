! rule: S6.3.2.2-004
! covers: error-stop
! evidence: positive-control
program error_stop_separator
  implicit none
  integer :: value
  value = 7
  if (.false.) error stop 1
  if (value /= 7) stop 2
end program
