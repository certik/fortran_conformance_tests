! rule: S6.3.2.2-002
! covers: format-spacing
! evidence: effect
program blank_runs_format
  implicit none
  character(len=2) :: compact, expanded
  write(compact, 100) 7
100 format(I2)
  write(expanded, 200) 7
200 format(I   2)
  if (compact /= ' 7') stop 1
  if (expanded /= ' 7') stop 2
  if (compact /= expanded) stop 3
end program
