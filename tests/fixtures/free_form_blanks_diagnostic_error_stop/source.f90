! rule: S6.3.2.2-004
! covers: error-stop
! evidence: effect
program error_stop_separator
  implicit none
  integer :: value
  value = 7
  if (.false.) errorstop 1 ! {error S6.3.2.2-004}
  if (value /= 7) stop 2
end program
