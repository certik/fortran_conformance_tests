! rule: S6.3.2.2-002
! covers: ordinary-statements
! evidence: effect
program blank_runs
  implicit none
  integer :: compact, expanded
  compact = 2 * 5 + 7
  expanded    =    2   *   5    +    7
  if (compact /= 17) stop 1
  if (expanded /= 17) stop 2
  if (compact /= expanded) stop 3
end program
