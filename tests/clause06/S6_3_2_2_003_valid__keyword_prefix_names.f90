! rule: S6.3.2.2-003
! covers: keyword-prefix-name-control
! evidence: positive-control
program keyword_prefix_names
  implicit none
  integer :: realx, stop0, goto10, endprogramx
  realx = 1
  stop0 = 2
  goto10 = 3
  endprogramx = 4
  if (realx + stop0 + goto10 + endprogramx /= 10) stop 1
end program
